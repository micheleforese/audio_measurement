from audio.model.sweep import SweepData
from pathlib import Path
from copy import deepcopy

home = Path(__file__).parent

balancer_csv = home / "Calibration balancer.csv"
pre_csv = home / "Calibration pre.csv"


balancer = SweepData.from_csv_file(balancer_csv)
pre = SweepData.from_csv_file(pre_csv)

# calibration_corrected = pre.data.sub(balancer.data, axis="dBV")deepcopy(pre)
calibration_corrected = deepcopy(pre)
calibration_corrected.data["dBV"] = pre.data["dBV"] - balancer.data["dBV"]
calibration_corrected_data = SweepData(calibration_corrected)
calibration_corrected_data.config.legend = (
    "Calibration corrected, Vpp IN=0.93 V, G=0.0 dB"
)
calibration_corrected_data.config.color = "#00ffff"


calibration_corrected_data.amplitude = 0.92848
calibration_corrected_data.save(balancer_csv.with_name("Calibration corrected.csv"))
