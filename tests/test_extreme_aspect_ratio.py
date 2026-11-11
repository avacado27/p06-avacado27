# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from os.path import abspath, dirname, join

from PIL import Image
from tornado.testing import AsyncHTTPTestCase

from thumbor.app import ThumborServiceApp
from thumbor.config import Config
from thumbor.context import Context
from thumbor.importer import Importer

COURSE_IMAGES_PATH = abspath(join(dirname(__file__), "../course/images/"))


class ExtremeAspectRatioTestCase(AsyncHTTPTestCase):
    def get_context(self):
        cfg = Config(
            SECURITY_KEY="ACME-SEC",
            ALLOW_UNSAFE_URL=True,
            ENGINE="thumbor.engines.pil",
            PILLOW_PRESERVE_INDEXED_MODE=True,
        )
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = COURSE_IMAGES_PATH
        cfg.STORAGE = "thumbor.storages.no_storage"
        cfg.RESULT_STORAGE = "thumbor.result_storages.no_storage"

        importer = Importer(cfg)
        importer.import_modules()
        return Context(config=cfg, importer=importer)

    def get_app(self):
        self.context = self.get_context()
        return ThumborServiceApp(self.context)

    def fetch_image(self, path):
        response = self.fetch(path)
        self.assertEqual(response.code, 200)
        return Image.open(BytesIO(response.body))

    def test_wide_transparent_png_800x20_returns_800x20(self):
        img = self.fetch_image("/unsafe/800x20/rainbow.png")

        self.assertEqual(img.size, (800, 20))

    def test_wide_transparent_png_800x20_is_not_blank(self):
        img = self.fetch_image("/unsafe/800x20/rainbow.png")
        alpha = img.convert("RGBA").getchannel("A")

        self.assertGreater(max(alpha.getdata()), 0)

    def test_fit_in_1x1_returns_1x1(self):
        img = self.fetch_image("/unsafe/fit-in/1x1/940x2.png")

        self.assertEqual(img.size, (1, 1))

    def test_fit_in_width_only_returns_100x1(self):
        img = self.fetch_image("/unsafe/fit-in/100x0/940x2.png")

        self.assertEqual(img.size, (100, 1))
