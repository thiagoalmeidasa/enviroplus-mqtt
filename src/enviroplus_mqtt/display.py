import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont


class Display:
    """ST7735 LCD on the Enviro+ board."""

    def __init__(self):
        self._disp = ST7735.ST7735(
            port=0,
            cs=1,
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=10000000,
        )

    def render_status(self, mqtt_broker: str, readings: dict, wifi_ssid) -> None:
        wifi_label = wifi_ssid if wifi_ssid else "disconnected"

        width = self._disp.width
        height = self._disp.height

        font = ImageFont.truetype(UserFont, 12)
        text_colour = (255, 255, 255)
        back_colour = (85, 15, 15) if wifi_label == "disconnected" else (0, 170, 170)

        message = f"Wi-Fi: {wifi_label}\nMQTT: {mqtt_broker}\nHumidity: {readings['humidity']}"

        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        size_x, size_y = draw.textsize(message, font)
        x = (width - size_x) / 2
        y = (height / 2) - (size_y / 2)
        draw.rectangle((0, 0, 160, 80), back_colour)
        draw.text((x, y), message, font=font, fill=text_colour)
        self._disp.display(img)
