# Solaris
A Discord bot designed to make your server a safer and better place.

# Cloning and running
I would greatly prefer if you invited Solaris to your server [here](https://discordapp.com/oauth2/authorize?client_id=661972684153946122&scope=bot&permissions=8) rather than run your own instance. With that being said, you are able to clone Solaris to your machine in order to test it or contribute.

Solaris was also not designed with universal compatibility in mind. If you want to include sections of Solaris' code in your own program, you will likely need to make significant modifications. Make sure you abide by the terms of the license, which you can find in LICENSE.

**Note:** As of v1.0.0-beta.3, these instructions haven't been fully tested. If they are wrong, open an issue.

## Running with Docker
**Warning**: Docker functionality in Solaris was designed specifically with Debian 10 Buster in mind. If you are using another OS, you may need to modify the Dockerfile.

### Requirements
- docker
- docker-compose

### Setup
1. `cd` into the root directory (the one with this README in it).
2. Run `mkdir secrets`.
3. Create a file called "token" in the "/secrets" directory.
4. Copy and paste your bot's token into the "token" file.
5. `cd` back into the root directory.
6. Run `docker-compose build`.

**Note:** You may need to create a `[root]/solaris/data/dynamic` directory for the build to be successful.

### Running
1. `cd` into the root directory (the one with this README in it).
2. Run `docker-compose up`.
    - To run silently, use the `-d` flag.

## Running inside a virtual environment
You should be able to run Solaris using this method on any OS.

### Requirements
- Python 3.8.0 or above

### Setup
1. `cd` into the root directory (the one with this README in it).
2. Create a file called ".env" in this directory.
3. Populate the ".env" file using the following template. Note that all but `TOKEN` are optional.
    ```
    TOKEN="xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxx"
    DEFAULT_PREFIX=">>"
    HUB_GUILD_ID=<guild id>
    HUB_COMMANDS_CHANNEL_ID=<channel id>
    HUB_RELAY_CHANNEL_ID=<channel id>
    HUB_STDOUT_CHANNEL_ID=<channel id>
    ```
4. Run `py -3 -m pip install poetry`.
    - You may need to use a different `pip` command depending on your Python configuration.
5. Run `py -3 -m venv ./.venv`.
6. Run `./.venv/Scripts/activate`.
7. Run `poetry install`.

### Running
1. `cd` into the root directory (the one with this README in it).
2. Run `py -3 -m solaris`.

# Links
[Invite Solaris to your server](https://discordapp.com/oauth2/authorize?client_id=661972684153946122&scope=bot&permissions=8) • [Invite Solaris to your server (non-admin privileges)](https://discordapp.com/oauth2/authorize?client_id=661972684153946122&scope=bot&permissions=403008598) • [Join the Solaris support server](https://discord.gg/c3b4cZs) • [See Solaris in action](https://discord.carberra.xyz)
