from enum import Enum
from typing import *
from omegaconf import DictConfig
import logging
import importlib
from torch_points3d.models.base_model import BaseModel
from torch_geometric.transforms import Compose
from torch_points3d.core.data_transform import XYZFeature, AddFeatsByKeys
from torch_points3d.utils.model_building_utils.model_definition_resolver import resolve

log = logging.getLogger(__name__)


class ModelArchitectures(Enum):
    UNET = "unet"
    ENCODER = "encoder"
    DECODER = "decoder"


def get_module_lib(module_name):
    # model_module = ".".join(["torch_points3d.applications", module_name])
    model_module = "torch_points3d.modules.KPConv"
    return importlib.import_module(model_module)


class Options:
    def __init__(self):
        pass


class ModelFactory:

    MODEL_ARCHITECTURES = [e.value for e in ModelArchitectures]

    @staticmethod
    def raise_enum_error(arg_name, arg_value, options):
        raise Exception("The provided argument {} with value {} isn't within {}".format(arg_name, arg_value, options))

    def __init__(
        self,
        architecture: str = None,
        input_nc: int = None,
        output_nc: int = None,
        num_layers: int = None,
        channel_nn: List[int] = None,
        config: DictConfig = None,
        **kwargs
    ):
        self._architecture = architecture.lower()
        assert self._architecture in self.MODEL_ARCHITECTURES, ModelFactory.raise_enum_error(
            "model_architecture", self._architecture, self.MODEL_ARCHITECTURES
        )
        self._input_nc = input_nc
        self._output_nc = output_nc
        self._num_layers = num_layers
        self._channel_nn = channel_nn
        self._config = config
        self._kwargs = kwargs

        if self._config:
            log.info("The config will be used to build the model")

    @property
    def modules_lib(self):
        raise NotImplementedError

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def num_layers(self):
        return self._num_layers

    @property
    def num_features(self):
        return self._input_nc

    def _build_unet(self):
        raise NotImplementedError

    def _build_encoder(self):
        raise NotImplementedError

    def _build_decoder(self):
        raise NotImplementedError

    def build(self):
        if self._architecture == ModelArchitectures.UNET.value:
            return self._build_unet()
        elif self._architecture == ModelArchitectures.ENCODER.value:
            return self._build_encoder()
        elif self._architecture == ModelArchitectures.DECODER.value:
            return self._build_decoder()
        else:
            raise NotImplementedError

    def resolve_model(self, model_config):
        """ Parses the model config and evaluates any expression that may contain constants
        Overrides any argument in the `define_constants` with keywords wrgument to the constructor
        """
        # placeholders to subsitute
        constants = {
            "FEAT": max(self.num_features, 0),
            "TASK": "segmentation",
        }

        # user defined contants to subsitute
        if "define_constants" in model_config.keys():
            constants.update(dict(model_config.define_constants))
            define_constants = model_config.define_constants
            for key in define_constants.keys():
                value = self.kwargs.get(key)
                if value:
                    constants[key] = value

        resolve(model_config, constants)