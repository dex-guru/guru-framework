from aiogram import Router

from bot_server.handlers import start


def get_handlers_router() -> Router:
    from . import (export_users, info, menu, artworks, support, tasks, account,
                   events, artworks, notifications, generate, stats, scan)
    """
        help - help
        account - manage account to access personalized features and settings
        events - view edit and delete events from their account
        artworks - manage uploaded artwork edit details and track engagement
        notifications - notifications for upcoming events reminders and updates
        tasks - tasklist management
        info - application info
        generate - generate t-shirt designs from their uploaded artwork and preview them before purchase
        stats - past orders sales statistics for vendors track shipments and access order details
        support - support contacts
    """

    router = Router()
    router.include_router(account.router)
    router.include_router(events.router)
    router.include_router(artworks.router)
    router.include_router(notifications.router)
    router.include_router(generate.router)
    router.include_router(tasks.router)
    router.include_router(info.router)
    router.include_router(start.router)
    router.include_router(support.router)
    router.include_router(scan.router)

    return router
