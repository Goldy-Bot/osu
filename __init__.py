from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Tuple

from typing import TypedDict

import io
import GoldyBot
from datetime import datetime
from GoldyBot import SlashOptionChoice

User = TypedDict(
    "User", 
    {
        "avatar_url": str,
        "country_code": str,
        "default_group": str,
        "id": int,
        "is_active": bool,
        "is_bot": bool,
        "is_deleted": bool,
        "is_online": bool,
        "is_supporter": bool,
        "last_visit": str,
        "pm_friends_only": bool,
        "username": str
    }
)

class BackgroundData(TypedDict):
    url: str
    user: User

class SeasonalBackgroundsResponseData(TypedDict):
    ends_at: str
    backgrounds: List[BackgroundData]


class Osu(GoldyBot.Extension):
    """Everything osu!"""
    def __init__(self):
        super().__init__()

        self.client = self.goldy.http_client._session

        self.seasonal_backgrounds_data: Tuple[int, SeasonalBackgroundsResponseData] = (0, {})

    async def dynamic_background_search(self, typing_value: str) -> List[SlashOptionChoice]:
        current_timestamp = datetime.now().timestamp()

        if current_timestamp > self.seasonal_backgrounds_data[0]:
            r = await self.client.get("https://osu.ppy.sh/api/v2/seasonal-backgrounds")
            data: SeasonalBackgroundsResponseData = await r.json()
            self.seasonal_backgrounds_data = (current_timestamp + 43200, data) # Expires in 12 hours.

        choices = []

        for index, background in enumerate(self.seasonal_backgrounds_data[1]["backgrounds"]):
            username = background["user"]["username"]

            if typing_value == str(index + 1) or typing_value in username or typing_value in ["", " "]:

                choices.append(
                    SlashOptionChoice(
                        name = f"Background #{index + 1} - {username}",
                        value = str(index)
                    )
                )

        return choices

    osu = GoldyBot.GroupCommand("osu", slash_cmd_only = True)

    @osu.sub_command(
        description = "Allows you to get a seasonal osu! background.", 
        slash_options = {
            "background_index": GoldyBot.SlashOptionAutoComplete(
                name = "background",
                description = "The seasonal background you would like to retrieve.", 
                callback = dynamic_background_search,
                required = True
            )
        },
        wait = True 
    )
    async def seasonal_background(self, platter: GoldyBot.GoldPlatter, background_index: str):
        background_index = int(background_index)
        background_data: BackgroundData = self.seasonal_backgrounds_data[1]["backgrounds"][background_index]

        r = await self.client.get(background_data["url"])

        image_bytes = await r.read()
        image = GoldyBot.File(io.BytesIO(image_bytes), file_name = "image.png")

        await platter.send_message(
            embeds = [
                GoldyBot.Embed(
                    title = f"Background #{background_index + 1}",
                    author = GoldyBot.EmbedAuthor(
                        name = background_data["user"]["username"],
                        url = f"https://osu.ppy.sh/users/{background_data['user']['id']}",
                        icon_url = background_data["user"]["avatar_url"]
                    ),
                    colour = GoldyBot.Colours.from_image(image),
                    image = GoldyBot.EmbedImage(background_data["url"])
                )
            ]
        )

load = lambda: Osu()