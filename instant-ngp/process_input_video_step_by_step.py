import os
import sys
import torch
from argparse import Namespace
from scripts.colmap2nerf import do_system, run_ffmpeg
import argparse
def parse_args():
	parser = argparse.ArgumentParser(
		description="Go step by stem to get separate frames from video, run colmap, get html visualization, run instant_ngp and video rendering"
	)

	parser.add_argument(
		"--input_video", required=True, help="vpath to video file, should be inside separate dir in the root of instant-ngp project"
	)
	parser.add_argument(
		"--fps", default=-1, help="fps value, output number of images depends on it"
	)

	parser.add_argument(
		"--stop_after", default=350, help="steps to do while training"
	)

	parser.add_argument(
		"--output_path", required=True, help="path where to put result html"
	)

	args = parser.parse_args()
	return args

def main():

	args = parse_args()

	print(f"{args.output_path = }")

	if not os.path.exists(args.input_video):
		print(f"Video {args.input_video} is not found!")
		sys.exit()


	input_dir = os.path.dirname(args.input_video)
	input_video_name = os.path.basename(args.input_video)

	project_root_dir = os.getcwd()
	os.chdir(input_dir)

	device = "cuda" if torch.cuda.is_available() else "cpu"


	duration = float(os.popen(f'ffprobe -i {input_video_name} -show_entries format=duration -v quiet -of csv="p=0"').read())
	# num_of_frames = int(os.popen(f'mediainfo --Output="Video;%FrameCount%" {input_video_name}').read())
	print(f"video duration = {duration}")

	if device == 'cuda':
		if args.fps != -1:
			do_system(f"python3 ../../instant-ngp/scripts/colmap2nerf.py --aabb_scale 4 --video_in {input_video_name} --video_fps {args.fps} --run_colmap --colmap_camera_model 'SIMPLE_PINHOLE' --colmap_matcher exhaustive --aabb_scale 16 --overwrite")
		else:
			new_fps = 40 / duration
			print("device cuda")
			print(f"{new_fps = }")
			do_system(f"python3 ../../instant-ngp/scripts/colmap2nerf.py --aabb_scale 4 --video_in {input_video_name} --video_fps {new_fps} --run_colmap --colmap_camera_model 'SIMPLE_PINHOLE' --colmap_matcher exhaustive --aabb_scale 16 --overwrite")

		os.chdir(project_root_dir)

		do_system(f"python3 instant-ngp/get_visualization_html.py --input_dir {input_dir}")
		# as a result {args.input_dir}/sfm_output.html is ready
		try:
			do_system(f"python3 instant-ngp/get_smooth_camera_path.py --input_dir {input_dir}")
		except:
			do_system(f"cp instant-ngp/data/nerf/fox/base_cam.json {os.path.join(input_dir, 'base_cam.json/')}")
		# as a result videos_as_input/base_cam.json is ready

		do_system(
			f"python3 instant-ngp/scripts/run.py --scene {input_dir} --n_steps {args.stop_after} "
			# f"--load_snapshot instant-ngp/base.ingp "
			f"--video_camera_path  {os.path.join(input_dir, 'base_cam.json')} "
			f"--video_fps 2 --video_n_seconds 10 --video_spp 1 "
			f"--video_output {os.path.join(input_dir, 'video.mp4')}  --width 1280 --height 720 "
			f"--save_mesh {os.path.join(input_dir, 'model.obj')} "
			f"--save_snapshot {os.path.join(input_dir, 'base.ingp')}")

		# as a resultvideos_as_input/video.mp4 and model.obj are ready
	else:
		if args.fps != -1:
			do_system(f"python3 ../scripts/colmap2nerf.py --video_in {input_video_name} --video_fps {args.fps} --overwrite")
		else:
			new_fps = 40 / duration
			print(f"{new_fps = }")
			print("device cpu")
			args_for_ffmpeg = Namespace(video_in=input_video_name, video_fps=new_fps, overwrite=True, images="images", time_slice="")
			run_ffmpeg(args_for_ffmpeg)

		os.chdir(project_root_dir)

		do_system(f"python3 instant-ngp/prepare_output_for_instant_ngp.py --dataset {input_dir} --output_path {args.output_path}")


if __name__ == "__main__":
	main()


# Just render without training
# python3 scripts/run.py --scene test_shevchenko_park --load_snapshot test_shevchenko_park/base.ingp --video_camera_path test_shevchenko_park/base_cam.json --video_fps 30 --video_n_seconds 10 --video_spp 10 --video_output test_shevchenko_park/video.mp4 --width 1280 --height 720 --train False
# python3 scripts/run.py --scene test_shevchenko_park --load_snapshot test_shevchenko_park/base.ingp --train False --save_mesh test_shevchenko_park/model.obj

# just show model
#  ./instant-ngp --scene test_shevchenko_park --load_snapshot test_shevchenko_park/base.ingp -- --no_train
