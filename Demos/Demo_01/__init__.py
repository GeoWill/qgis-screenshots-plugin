from screenshots.session import Session, Step
from screenshots.utils import setActiveLayer, layerActive, addLayer#, openProject
from qgis.utils import iface
from screenshots import addSessionModule
from screenshots.screenshot import Screenshot

screenshots = Screenshot()

screenshots.saveDirectory = sessionDataFolder()

session = Session("Demo 01", "Demos", "The first Demo using QGIS test data")
session.addStep("Start", "Take Screenshots for first Demo", steptype=Step.MANUALSTEP)
session.addStep("Load Rivers", "Loading rivers.shp from training data",
    function=lambda: addLayer("/home/will/foss/qgis/QGIS-Training-Data/exercise_data/shapefile/places.shp"))

session.addStep("Finish", "Screenshot session for first Demo finished", steptype=Step.MANUALSTEP)
