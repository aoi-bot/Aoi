## Code Style
-  Any code submitted must pass flake8
-  The configuration file is included, just running `flake8` in the project directory is enough to check.

## Custom Commands
- The custom command format is used to add custom commands that behave just like a regular command.
```yaml
--
trigger_name:
    responses:
      - "I am a sample text response!"
      - "{user} did the command, tagging {target}!"
    images:
      - "https://random.com/image2.png"
```
- A random image and text is picked from the command spec

## Context `send_xxxx` methods
- `send_ok` is used when a user has *confirmed* an action.
- `send_error` is used when a user *cancels* an action or an error happens
- `send_info` is used for anything else

## Errors
- Check to see if your error is handled in the error handler *before* you catch it, in order to 
  maintain consistency
- Be concise: Don't print a massive stack trace. Give the user enough information on what the 
  problem was, and enough information to fix it.
  - Don't just say "An error happened" if you don't know the root cause. If it's an error
    related to something *outside* Aoi, then let the user know it was an *unexpected error*

## Code Placement and Abstractions
Certain types of code belongs in certain places
```
wrappers/  # where API wrappers go
    example/
        __init__.py  # all wrappers should be importable as `import x from wrapper_name`
        file1.py
        file2.py
loaders/  # where custom commands go
libs/  # reusable code goes here
cogs/  # Aoi's modules go here
assets/  # Any assets used by Aoi go here
```

`extensions.yaml` defines the cogs loaded with Aoi
```yaml
"ServerManagement":  # the category the module shows up in under `,mdls`
    "cogs.administration.roles": "Roles"  # 1: the path to the cog, as if you were importing
                                          # 2: the *exact* name of the class of the cog 
    "cogs.administration.channels": "Channels"
    "cogs.administration.permissions": "Permissions"
    "cogs.administration.welcomegoodbye": "WelcomeGoodbye"
...
```
The cog class name is what's exposed to the user as the module name, so make sure it describes the cog

*Before making another cog*, see if your command fits somewhere else *first*
