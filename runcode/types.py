from .AAA3A_utils import CogsUtils, Menu  # isort:skip
from redbot.core import commands  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import aiohttp
import datetime
import json
import time
import zlib
from dataclasses import dataclass
from functools import partial
from humanfriendly import format_timespan

from redbot.core.utils.chat_formatting import box, pagify

from .data import LANGUAGES_IDENTIFIERS, LANGUAGES_IMAGES


@dataclass(frozen=True)
class WandboxEngine:
    name: str
    version: str
    template: str
    language: str
    compiler_option_raw: bool
    runtime_option_raw: bool
    display_compile_command: bool


@dataclass(frozen=True)
class WandboxRequest:
    cog: commands.Cog
    engine: WandboxEngine
    # Web request
    code: str
    save: bool
    stdin: str
    compiler_options: str
    runtime_options: str

    def to_request_parameters(self):
        # parameters = {
        #     "code": parameters["code"],
        #     "codes": parameters["codes"] if "codes" in parameters else [],
        #     "compiler": parameters["engine"],
        #     "save": True,
        #     "stdin": parameters["input"] if "input" in parameters else "",
        #     "compiler-option-raw": parameters["compiler-options"],
        #     "runtime-option-raw": parameters["runtime-options"]
        # }
        return {
            "code": self.code,
            "compiler": self.engine.name,  # self.compiler,
            "save": self.save,
            "stdin": self.stdin,
            "compiler-option-raw": self.compiler_options,
            "runtime-option-raw": self.runtime_options
        }

    def to_embed(self, with_code: typing.Optional[bool] = False) -> discord.Embed:
        embed: discord.Embed = discord.Embed(title="RunCode Request (with Wandbox API)", color=discord.Color.green())
        embed.set_author(name=f"{self.engine.language.capitalize()} language", icon_url=LANGUAGES_IMAGES[self.language.language])
        if with_code:
            if self.codes == []:
                description = box(self.code, lang=LANGUAGES_IDENTIFIERS[self.engine.language][0])
            else:
                description = "\n".join([box(code, lang=LANGUAGES_IDENTIFIERS[self.engine.language][0]) for code in self.codes])
            pages = list(pagify(description, delims=["\n"], page_length=4000))
            if len(pages) == 1:
                embed.description = description
            else:
                page = pages[0]
                if page.endswith("```"):
                    page[:-3]
                embed.description = f"{page}\n...```"
        for field in ["language", "compiler", "save", "stdin", "compiler_option_raw", "runtime_option_raw"]:
            embed.add_field(name=field, value=box(f"{repr(getattr(self, field))}", lang="py"))
        return embed

    async def fetch_response(self, raw: typing.Optional[bool] = False) -> "WandboxResponse":
        start = time.monotonic()
        data = json.dumps(self.to_request_parameters())
        async with self.cog._session.post(url="https://wandbox.org/api/compile.json", data=data, headers={"content-type": "text/javascript"}) as r:
            try:
                raw_response = await r.json()
            except (aiohttp.ContentTypeError, json.JSONDecodeError):
                error = await r.text(encoding="utf-8")
            else:
                error = None
            if error is not None:
                raise RuntimeError(error)
        end = time.monotonic()
        for key, value in raw_response.items():
            if isinstance(value, str):
                raw_response[key] = value.replace("/home/jail", "{HOME}")
        if raw:
            return raw_response
        if "status" not in raw_response:
            raw_response["status"] = None
        if "signal" not in raw_response:
            raw_response["signal"] = None
        response = WandboxResponse(request=self, run_time=int(end - start), **raw_response)
        return response


@dataclass(frozen=True)
class WandboxResponse:
    request: WandboxRequest
    run_time: int
    # Web request
    status: str
    signal: str
    compiler_output: str
    compiler_error: str
    compiler_message: str
    program_output: str
    program_error: str
    program_message: str
    permlink: str
    url: str

    async def send(self, ctx: commands.Context, verbose: typing.Optional[bool] = False) -> None:
        if not verbose and not (self.signal or self.compiler_error or self.program_error or self.status != "0"):
            output = f"{self.url}\n" + self.program_output
            await Menu(pages=output, box_language_py=True).start(ctx)
            return
        embed: discord.Embed = discord.Embed(title=f"RunCode Response (with Wandbox API)", url=self.url)
        embed.timestamp = datetime.datetime.utcnow()
        run_time = format_timespan(self.run_time)
        embed.set_footer(text=f"Ran in {run_time}.")
        embed.set_author(name=f"{self.request.engine.language.capitalize()} language", icon_url=LANGUAGES_IMAGES[self.request.engine.language])
        if self.signal or self.compiler_error or self.program_error:
            if not self.status or self.status != "0":
                embed.color = discord.Color.red()
            else:
                embed.color = discord.Color.orange()
        elif self.status != "0":
            embed.color = discord.Color.orange()
        else:
            embed.color = discord.Color.green()

        embed.add_field(name="Engine used", value=self.request.engine.name, inline=True)
        embed.add_field(
            name="Command used",
            value=self.request.cog.wandbox_languages[self.request.engine.language][self.request.engine.template][self.request.engine.name].display_compile_command + (f" {self.request.compiler_options}" if self.request.compiler_options else "") + (f" {self.request.runtime_options}" if self.request.runtime_options else ""),
            inline=True
        )
        embed.add_field(name="Exit status", value=self.status, inline=False)
        description = ""
        for field in ["signal", "compiler_output", "compiler_error", "program_output", "program_error"]:
            if value := getattr(self, field):
                description += f"\n\n**{field.replace('_', ' ').title()}**:\n{value}"
        pages = list(pagify(description, page_length=4000 if (6000 - len(embed) > 4000) else (6000 - len(embed) > 4000)))
        embeds = []
        for page in pages:
            e = embed.copy()
            e.description = page
            embeds.append(e)
        await Menu(pages=embeds).start(ctx)


@dataclass(frozen=True)
class TioLanguage:
    name: str
    link: str
    prettify: str
    value: typing.Dict[str, typing.Any]


@dataclass(frozen=True)
class TioRequest:
    cog: commands.Cog
    language: TioLanguage
    # Web request
    code: str
    inputs: typing.List[str]
    compiler_flags: typing.List[str]
    command_line_options: typing.List[str]
    args: typing.List[str]

    def to_request_parameters(self):
        # parameters = {
        #     "code": self.code,
        #     "lang": self.language,
        #     "inputs": self.inputs,
        #     "compilerFlags": self.compiler_flags,
        #     "commandLineOptions": self.command_line_options,
        #     "args": self.args
        # }
        parameters = {
            "lang": [self.language.value],
            ".code.tio": self.code,
            ".input.tio": self.inputs,
            "TIO_CFLAGS": self.compiler_flags,
            "TIO_OPTIONS": self.command_line_options,
            "args": self.args
        }
        return parameters

    def to_embed(self, with_code: typing.Optional[bool] = False) -> discord.Embed:
        embed: discord.Embed = discord.Embed(title="RunCode Request (with Tio API)", color=discord.Color.green())
        embed.set_author(name=f"{self.language.name.capitalize()} language")
        if with_code:
            description = box(self.code, lang=self.language)
            pages = list(pagify(description, delims=["\n"], page_length=4000))
            if len(pages) == 1:
                embed.description = description
            else:
                page = pages[0]
                if page.endswith("```"):
                    page[:-3]
                embed.description = f"{page}\n...```"
        for field in ["lang", "inputs", "compiler_flags", "command_line_options", "args"]:
            embed.add_field(name=field, value=box(f"{repr(getattr(self, field))}", lang="py"))
        return embed

    async def fetch_response(self) -> "TioResponse":
        start = time.monotonic()
        to_bytes = partial(bytes, encoding='utf-8')
        def _to_tio_string(couple):
            name, obj = couple[0], couple[1]
            if not obj:
                return b""
            elif type(obj) == list:
                content = ["V" + name, str(len(obj))] + obj
                return to_bytes("\x00".join(content) + "\x00")
            else:
                return to_bytes(f"F{name}\x00{len(to_bytes(obj))}\x00{obj}\x00")
        strings = self.to_request_parameters()
        bytes_ = b"".join(map(_to_tio_string, zip(strings.keys(), strings.values()))) + b"R"
        data = zlib.compress(bytes_, 9)[2:-4]
        async with self.cog._session.post("https://tio.run/cgi-bin/run/api/", data=data) as r:
            raw_response: str = await r.text(encoding="utf-8")
            raw_response = raw_response.replace(raw_response[:16], '')  # remove token
        end = time.monotonic()
        response = TioResponse(request=self, run_time=int(end - start), result=raw_response)
        return response


@dataclass(frozen=True)
class TioResponse:
    request: TioRequest
    run_time: int
    # Web request
    result: str

    async def send(self, ctx: commands.Context, verbose: typing.Optional[bool] = False) -> None:
        output = self.result
        if not verbose:
            try:
                start = output.rindex("Real time: ")
                end = output.rindex("%\nExit code: ")
                output = output[:start] + output[end + 2:]
            except ValueError:
                pass
            output = CogsUtils().replace_var_paths(output)
            await Menu(pages=output, box_language_py=True).start(ctx)
            return
        embed: discord.Embed = discord.Embed(title=f"RunCode Response (with Tio API)", url=self.request.language.link)
        embed.timestamp = datetime.datetime.utcnow()
        run_time = format_timespan(self.run_time)
        embed.set_footer(text=f"Ran in {run_time}.")
        embed.set_author(name=f"{self.request.language.name.capitalize()} language")
        try:
            start = output.rindex("Real time: ")
            end = output.rindex("%\nExit code: ")
            description = output[:start] + output[end + 2:]
            debug = output[start:end + 2]
        except ValueError:
            pass
        embed.add_field(name="Debug", value=box(debug, lang="py"))
        pages = list(pagify(description, page_length=4000 if (6000 - len(embed) > 4000) else (6000 - len(embed) > 4000)))
        embeds = []
        for page in pages:
            e = embed.copy()
            e.description = page
            embeds.append(e)
        await Menu(pages=embeds).start(ctx)
