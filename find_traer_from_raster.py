"""
Model exported as python.
Name : Find tree from RGB raster
Group : Class2025
With QGIS : 34404
"""

from typing import Any, Optional

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingFeedback, QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis import processing


class FindTreeFromRgbRaster(QgsProcessingAlgorithm):

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(QgsProcessingParameterRasterLayer('rgb_raster', 'RGB Raster', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Result', 'Result', type=QgsProcessing.TypeVectorPoint, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters: dict[str, Any], context: QgsProcessingContext, model_feedback: QgsProcessingFeedback) -> dict[str, Any]:
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(6, model_feedback)
        results = {}
        outputs = {}

        # Raster calculator VARI
        alg_params = {
            'CELL_SIZE': None,
            'CREATION_OPTIONS': None,
            'CRS': None,
            'EXPRESSION': '("A@2"-"A@1")/("A@2"+"A@1"-"A@3")\n',
            'EXTENT': None,
            'LAYERS': parameters['rgb_raster'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculatorVari'] = processing.run('native:modelerrastercalc', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Raster calculator VARI >0.001
        alg_params = {
            'CELL_SIZE': None,
            'CREATION_OPTIONS': None,
            'CRS': None,
            'EXPRESSION': '"A@1"  >=  0.001',
            'EXTENT': None,
            'LAYERS': outputs['RasterCalculatorVari']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculatorVari0001'] = processing.run('native:modelerrastercalc', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Polygonize (raster to vector)
        alg_params = {
            'BAND': 1,
            'EIGHT_CONNECTEDNESS': False,
            'EXTRA': None,
            'FIELD': 'DN',
            'INPUT': outputs['RasterCalculatorVari0001']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolygonizeRasterToVector'] = processing.run('gdal:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Extract by expression "DN"=1 and $area > 0.004

        alg_params = {
            'EXPRESSION': '"DN"=1 and $area > 0.004\r\n',
            'INPUT': outputs['PolygonizeRasterToVector']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByExpressionDn1AndArea0004'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Buffer 10 cm dissolved
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': 0.1,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['ExtractByExpressionDn1AndArea0004']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer10CmDissolved'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Centroids from buffer
        alg_params = {
            'ALL_PARTS': True,
            'INPUT': outputs['Buffer10CmDissolved']['OUTPUT'],
            'OUTPUT': parameters['Result']
        }
        outputs['CentroidsFromBuffer'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Result'] = outputs['CentroidsFromBuffer']['OUTPUT']
        
        feedback.pushInfo(str(results['Result']))

        #results['Result'].renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Star)
        return results

    def name(self) -> str:
        return 'Find tree from RGB raster'

    def displayName(self) -> str:
        return 'Find tree from RGB raster'

    def group(self) -> str:
        return 'Class2025'

    def groupId(self) -> str:
        return 'Class2025'

    def createInstance(self):
        return self.__class__()
