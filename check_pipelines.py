import inspect

from app.ai.pipelines.model_a_understanding import RoomUnderstandingPipeline
from app.ai.pipelines.model_b_segmentation import RoomSegmentationPipeline
from app.ai.pipelines.model_e_depth import DepthEstimationPipeline

for cls in (RoomUnderstandingPipeline, RoomSegmentationPipeline, DepthEstimationPipeline):
    print(cls.__name__, inspect.signature(cls.__init__))
