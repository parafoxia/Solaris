from asyncio import TimeoutError
from datetime import datetime, timedelta

from s4.utils import chron


class Menu:
    def __init__(self, ctx, start_key, stop_key=None, timeout_key=None):
        self.ctx = ctx
        self.bot = ctx.bot
        self.start_key = start_key
        self.stop_key = stop_key
        self.timeout_key = timeout_key
        self.message = None

    async def start(self, **kwargs):
        self.message = await self.ctx.send(embed=self.bot.embed.load(self.start_key, ctx=self.ctx, **kwargs))

    async def stop(self, **kwargs):
        if self.stop_key is not None:
            await self.switch(self.stop_key, clear_reactions=True, **kwargs)
        else:
            await self.message.delete()

    async def timeout(self, **kwargs):
        if self.timeout_key is not None:
            length = kwargs.get("length", None)
            await self.switch(self.timeout_key, clear_reactions=True, length=length, **kwargs)
        else:
            await self.stop(**kwargs)

    async def switch(self, key, clear_reactions=False, **kwargs):
        if clear_reactions:
            await self.message.clear_reactions()

        await self.message.edit(embed=self.bot.embed.load(key, ctx=self.ctx, **kwargs))

    def __repr__(self):
        return (
            f"<Menu start_key={self.start_key!r}"
            f" stop_key={self.stop_key!r}"
            f" timeout_key={self.timeout_key!r}"
            f" message={self.message!r}>"
        )


class Selection:
    def __init__(self, menu, selection, *, timeout=300.0, auto_exit=True, check=None):
        self.menu = menu
        self.timeout = timeout
        self.auto_exit = auto_exit
        self.check = check or self._default_check

        self._base_selection = selection

    @property
    def selection(self):
        return self._base_selection

    @selection.setter
    def selection(self, value):
        self._base_selection = value

    def _default_check(self, reaction, user):
        return (
            reaction.message.id == self.menu.message.id
            and user == self.menu.ctx.author
            and reaction.emoji.name in self.selection
        )

    async def _serve(self):
        await self.menu.message.clear_reactions()

        for e in self.selection:
            await self.menu.message.add_reaction(self.menu.bot.emoji.get(e))

    async def response(self):
        await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(length=chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji.name) == "exit" and self.auto_exit:
                await self.menu.stop()
            else:
                return r

    def __repr__(self):
        return f"<Selection timeout={self.timeout!r} auto_exit={self.auto_exit!r} menu={self.menu!r}>"


class SelectionMenu(Menu):
    def __init__(
        self, ctx, selection, start_key, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(ctx, start_key, stop_key, timeout_key)
        self.selection = Selection(self, selection, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self, **kwargs):
        await super().start(**kwargs)
        return await self.selection.response()

    def __repr__(self):
        return (
            f"<SelectionMenu start_key={self.start_key!r}"
            f" stop_key={self.stop_key!r}"
            f" timeout_key={self.timeout_key!r}"
            f" selection={self.selection!r}"
            f" message={self.message!r}>"
        )


class NumberedSelection(Selection):
    def __init__(self, menu, iterable, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["exit"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.iterable = iterable
        self.max_page = (len(iterable) // 9) + 1
        self.pages = [{} for i in range(self.max_page)]

        self._selection = []
        self._last_selection = []
        self._page = 0

        for i, obj in enumerate(iterable):
            self.pages[i // 9].update({f"option{(i % 9) + 1}": obj})

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    @property
    def table(self):
        return "\n".join(f"{self.menu.bot.emoji.mention(k)} {v}" for k, v in self.pages[self.page].items())

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pages) > 1:
            if self.page != 0:
                s.insert(0, "pageback")
                s.insert(0, "stepback")
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "stepnext")
                s.insert(insert_point, "pagenext")

        for i in range(len(self.pages[self.page])):
            s.insert(i + insert_point, f"option{i + 1}")

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(length=chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji.name) == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page
            else:
                return self.pages[self.page][r]

            await self.menu.switch_page()
            await self.menu.message.remove_reaction(reaction, self.menu.ctx.author)
            return await self.response()

    def __repr__(self):
        return (
            f"<NumberedSelection timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" page={self.page!r}"
            f" max_page={self.max_page!r}"
            f" menu={self.menu!r}>"
        )


class NumberedSelectionMenu(Menu):
    def __init__(
        self, ctx, iterable, start_key, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(ctx, start_key, stop_key, timeout_key)
        self.selection = NumberedSelection(self, iterable, timeout=timeout, auto_exit=auto_exit, check=check)

        self._options = {}

    @property
    def page_fields(self):
        return [(f"{self.selection.page_info}", f"{self.selection.table}", False)]

    async def start(self, **kwargs):
        self._options = kwargs
        await super().start(fields=self.page_fields, **kwargs)
        return await self.selection.response()

    async def switch_page(self):
        await self.switch(self.start_key, fields=self.page_fields, **self._options)

    def __repr__(self):
        return (
            f"<NumberedSelectionMenu start_key={self.start_key!r}"
            f" stop_key={self.stop_key!r}"
            f" timeout_key={self.timeout_key!r}"
            f" selection={self.selection!r}"
            f" message={self.message!r}>"
        )


class PageControls(Selection):
    def __init__(self, menu, pages, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["exit"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.pages = pages
        self.max_page = len(pages)

        self._selection = []
        self._last_selection = []
        self._page = 0

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pages) > 1:
            if self.page != 0:
                s.insert(0, "pageback")
                s.insert(0, "stepback")
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "stepnext")
                s.insert(insert_point, "pagenext")

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(length=chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji.name) == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page

            await self.menu.switch(self.pages[self.page], **self.menu._options)
            await self.menu.message.remove_reaction(reaction, self.menu.ctx.author)
            return await self.response()

    def __repr__(self):
        return f"<PageControls>"


class MultiPageMenu(Menu):
    def __init__(self, ctx, pages, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(ctx, pages[0], stop_key, timeout_key)
        self.selection = PageControls(self, pages, timeout=timeout, auto_exit=auto_exit, check=check)

        self._options = {}

    async def start(self, **kwargs):
        self._options = kwargs
        await super().start(**kwargs)
        return await self.selection.response()

    def __repr__(self):
        return (
            f"<MultiPagedMenu start_key={self.start_key!r}"
            f" stop_key={self.stop_key!r}"
            f" timeout_key={self.timeout_key!r}"
            f" selection={self.selection!r}"
            f" message={self.message!r}>"
        )
