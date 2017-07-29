import logging

logger = logging.getLogger(__name__)


def start(token, client_id, google_api_key, loop):
    import discord
    import asyncio

    # Create client
    logger.debug("Creating Discord client")
    asyncio.set_event_loop(loop)
    client = discord.Client()
    from . import _client
    _client.client = client

    # Save key info to data
    from .. import datatools
    data = datatools.get_data()
    data["discord"]["token"] = token
    data["discord"]["client_id"] = client_id
    data["discord"]["google_api_key"] = google_api_key
    datatools.write_data(data)

    # Import event handlers
    logger.info("Importing event handlers")
    event_handlers = _get_event_handlers()

    # Create event handler combiner
    logger.debug("Compiling event handlers")

    def create_event_handler(event_handler_type):
        async def func(*args, **kwargs):
            for module_event_handler in event_handlers[event_handler_type]:
                module_event_handler_func = getattr(module_event_handler, event_handler_type)
                await module_event_handler_func(*args, **kwargs)
        func.__name__ = event_handler_type
        return func

    # Register event handlers
    logger.debug("Registering event handlers into client")
    for event_handler in event_handlers.keys():
        client.event(create_event_handler(event_handler))

    # Run the client loop
    logger.debug("Connecting to Discord")
    try:
        client.loop.run_until_complete(client.login(token))
    except:
        logger.critical("Could not connect to Discord")
    else:
        logger.debug("Running the bot")
        try:
            client.loop.run_until_complete(client.connect())
        except KeyboardInterrupt:
            client.loop.run_until_complete(client.logout())
            pending = asyncio.Task.all_tasks(loop=client.loop)
            gathered = asyncio.gather(*pending, loop=client.loop)
            try:
                gathered.cancel()
                client.loop.run_until_complete(gathered)

                # we want to retrieve any exceptions to make sure that
                # they don't nag us about it being un-retrieved.
                gathered.exception()
            except:
                pass
        finally:
            logger.critical("Bot stopped")
            client.loop.close()


def _get_event_handlers():
    """Gets dictionary of event handlers and the modules that define them

    Returns:
        event_handlers (dict): Contains "all", "on_ready", "on_message", "on_reaction_add", "on_error"
    """

    import os
    import importlib

    event_handlers = {
        "on_ready": [],
        "on_resume": [],
        "on_error": [],
        "on_message": [],
        "on_socket_raw_receive": [],
        "on_socket_raw_send": [],
        "on_message_delete": [],
        "on_message_edit": [],
        "on_reaction_add": [],
        "on_reaction_remove": [],
        "on_reaction_clear": [],
        "on_channel_delete": [],
        "on_channel_create": [],
        "on_channel_update": [],
        "on_member_join": [],
        "on_member_remove": [],
        "on_member_update": [],
        "on_server_join": [],
        "on_server_remove": [],
        "on_server_update": [],
        "on_server_role_create": [],
        "on_server_role_delete": [],
        "on_server_role_update": [],
        "on_server_emojis_update": [],
        "on_server_available": [],
        "on_server_unavailable": [],
        "on_voice_state_update": [],
        "on_member_ban": [],
        "on_member_unban": [],
        "on_typing": [],
        "on_group_join": [],
        "on_group_remove": []
    }

    # Iterate through module folders
    database_dir = "{}/modules".format(os.path.dirname(os.path.realpath(__file__)))
    for module_name in os.listdir(database_dir):
        module_dir = "{}/{}".format(database_dir, module_name)

        # Iterate through files in module
        if os.path.isdir(module_dir) and not module_name.startswith("_"):

            # Add all defined event handlers in module files
            module_event_handlers = os.listdir(module_dir)

            for event_handler in event_handlers.keys():
                if "{}.py".format(event_handler) in module_event_handlers:
                    import_name = ".discord_modis.modules.{}.{}".format(module_name, event_handler)
                    logger.info("Found event handler {}".format(import_name[23:]))

                    event_handlers[event_handler].append(importlib.import_module(import_name, "modis"))

    return event_handlers