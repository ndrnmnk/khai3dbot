import argparse
import json
import numpy as np
import os
from scipy.spatial.transform import Rotation as R

def parse_args():
    parser = argparse.ArgumentParser(
        description="Get smooth camera path as base_cam.json"
    )
    parser.add_argument(
        "--input_dir", required=True, help="path to input folder with model files"
    )

    args = parser.parse_args()
    return args

def nerf_to_ngp(xf):
	mat = np.copy(xf)
	mat = mat[:-1, :]
	mat[:, 1] *= -1  # flip axis
	mat[:, 2] *= -1
	mat[:, 3] *= 0.33  # scale
	mat[:, 3] += [0.5, 0.5, 0.5]  # offset

	mat = mat[[1, 2, 0], :]  # swap axis

	rm = R.from_matrix(mat[:, :3])

	# quaternion (x, y, z, w) and translation
	return rm.as_quat(), mat[:, 3] + 0.025

def smooth_camera_path(path_to_transforms, ):
	out = {"path": [], "time": 1.0}
	with open(os.path.join(path_to_transforms, 'transforms.json')) as f:
		data = json.load(f)

	n_frames = len(data['frames'])

	xforms = {}
	for i in range(n_frames):
		file = int(data['frames'][i]['file_path'].split('/')[-1][:-4])
		xform = data['frames'][i]['transform_matrix']
		xforms[file] = xform

	xforms = dict(sorted(xforms.items()))

	# linearly take 10 transformation from transfroms.json
	for ind in np.linspace(min(xforms), max(xforms), 10, endpoint=True, dtype=int):
		q, t = nerf_to_ngp(np.array(xforms[ind]))

		out['path'].append({
			"R": list(q),
			"T": list(t),
			"dof": 0.0,
			"fov": 43,
			"scale": 0,
			"slice": 0.0
		})

	with open(path_to_transforms + '/base_cam.json', "w") as outfile:
		json.dump(out, outfile, indent=2)

def main():
	args = parse_args()

	smooth_camera_path(args.input_dir)

if __name__ == "__main__":
    main()