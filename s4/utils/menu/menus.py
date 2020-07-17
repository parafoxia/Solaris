from s4.utils.menu import selectors


class Menu:
    def __init__(self, ctx, start_pagemap, stop_pagemap={}, timeout_pagemap={}):
        self.ctx = ctx
        self.bot = ctx.bot
        self.start_pagemap = start_pagemap
        self.stop_pagemap = stop_pagemap
        self.timeout_pagemap = timeout_pagemap

    async def start(self):
        self.message = await self.ctx.send(embed=self.bot.embed.build(ctx=self.ctx, **self.start_pagemap))

    async def stop(self):
        if self.stop_pagemap:
            await self.message.clear_reactions()
            await self.message.edit(embed=self.bot.embed.build(ctx=self.ctx, **self.stop_pagemap))
        else:
            await self.message.delete()

    async def timeout(self):
        if self.timeout_pagemap:
            length = kwargs.get("length", None)
            await self.message.clear_reactions()
            await self.message.edit(embed=self.bot.embed.build(ctx=self.ctx, length=length, **self.timeout_pagemap))
        else:
            await self.stop()

    async def switch(self, pagemap=None):
        await self.message.edit(embed=self.bot.embed.build(ctx=self.ctx, **(pagemap or self.start_pagemap)))

    def __repr__(self):
        return (
            f"<Menu"
            f" message={self.message!r}>"
        )


class SelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        selection,
        start_pagemap,
        stop_pagemap={},
        timeout_pagemap={},
        *,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, start_pagemap, stop_pagemap, timeout_pagemap)
        self.selector = selectors.Selector(self, selection, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    def __repr__(self):
        return (
            f"<SelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )


class KeySelectionMenu(SelectionMenu):
    def __init__(
        self, ctx, selection, start_key, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(
            ctx,
            selection,
            ctx.bot.embed.get_pagemap(start_key),
            ctx.bot.embed.get_pagemap(stop_key),
            ctx.bot.embed.get_pagemap(timeout_key),
            timeout=timeout,
            auto_exit=auto_exit,
            check=check,
        )

    def __repr__(self):
        return (
            f"<KeySelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )


class NumberedSelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        iterable,
        start_pagemap,
        stop_pagemap={},
        timeout_pagemap={},
        *,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, start_pagemap, stop_pagemap, timeout_pagemap)
        self.selector = selectors.NumericalSelector(self, iterable, timeout=timeout, auto_exit=auto_exit, check=check)

    @property
    def page_field(self):
        return (f"{self.selector.page_info}", f"{self.selector.table}", False)

    async def start(self):
        self.start_pagemap.update({"fields": [self.page_field]})
        await super().start()
        return await self.selector.response()

    async def switch(self, reaction):
        self.start_pagemap.update({"fields": [self.page_field]})
        await super().switch()
        await self.message.remove_reaction(reaction, self.ctx.author)

    def __repr__(self):
        return (
            f"<NumberedSelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )


class NumberedKeySelectionMenu(NumberedSelectionMenu):
    def __init__(
        self, ctx, iterable, start_key, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(
            ctx,
            iterable,
            ctx.bot.embed.get_pagemap(start_key),
            ctx.bot.embed.get_pagemap(stop_key),
            ctx.bot.embed.get_pagemap(timeout_key),
            timeout=timeout,
            auto_exit=auto_exit,
            check=check,
        )

    def __repr__(self):
        return (
            f"<NumberedKeySelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )


class MultiPageMenu(Menu):
    def __init__(
        self, ctx, pagemaps, stop_pagemap={}, timeout_pagemap={}, *, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(ctx, pagemaps[0], stop_pagemap, timeout_pagemap)
        self.selector = selectors.PageControls(self, pagemaps, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    async def switch(self, reaction):
        await super().switch(self.selector.pagemaps[self.selector.page])
        await self.message.remove_reaction(reaction, self.ctx.author)

    def __repr__(self):
        return (
            f"<MultiPageMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )


class MultiPageKeyMenu(MultiPageMenu):
    def __init__(self, ctx, keys, stop_key=None, timeout_key=None, *, timeout=300.0, auto_exit=True, check=None):
        pagemaps = [ctx.bot.embed.get_pagemap(key) for key in keys]
        super().__init__(
            ctx,
            pagemaps,
            ctx.bot.embed.get_pagemap(stop_key),
            ctx.bot.embed.get_pagemap(timeout_key),
            timeout=timeout,
            auto_exit=auto_exit,
            check=check,
        )

    def __repr__(self):
        return (
            f"<MultiPageKeyMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" message={self.message!r}>"
        )
