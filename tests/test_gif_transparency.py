# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from os.path import abspath, dirname, join
from unittest import TestCase

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

COURSE_IMAGES_PATH = abspath(join(dirname(__file__), "../course/images/"))


def count_transparent_pixels(img):
    alpha = img.convert("RGBA").getchannel("A")
    return sum(1 for value in alpha.getdata() if value < 255)


class GifTransparencyTestCase(TestCase):
    def get_context(self):
        cfg = Config(
            SECURITY_KEY="ACME-SEC",
            ENGINE="thumbor.engines.pil",
            PILLOW_PRESERVE_INDEXED_MODE=True,
        )
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = COURSE_IMAGES_PATH
        cfg.STORAGE = "thumbor.storages.no_storage"

        return Context(config=cfg)

    def resize_gif(self, buffer, size):
        engine = Engine(self.get_context())
        engine.load(buffer, ".gif")
        engine.resize(*size)

        return Image.open(BytesIO(engine.read(".gif")))

    def test_resized_sticker_keeps_transparent_pixels(self):
        with open(join(COURSE_IMAGES_PATH, "sticker.gif"), "rb") as f:
            buffer = f.read()

        with Image.open(BytesIO(buffer)) as source:
            assert source.info.get("transparency") is not None

        img = self.resize_gif(buffer, (240, 160))

        assert img.format == "GIF"
        assert img.info.get("transparency") is not None
        assert count_transparent_pixels(img) > 0

    def test_resized_opaque_gif_stays_opaque(self):
        source = Image.new("RGB", (64, 64), (200, 30, 30)).convert("P")
        out = BytesIO()
        source.save(out, "GIF")

        img = self.resize_gif(out.getvalue(), (32, 32))

        assert img.format == "GIF"
        assert img.info.get("transparency") is None
        assert count_transparent_pixels(img) == 0
