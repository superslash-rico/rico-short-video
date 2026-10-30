#!/usr/bin/env python3
"""Check small bright-point contrast in reviewed clean background ROIs.

This is an advisory signal check, not an aesthetic or glow classifier.
Release checks expect points in every sample. Known negatives require --regression.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageFilter
except ImportError:
    raise SystemExit('CHECK NOT RUN: Pillow is required; do not record a pass.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def run(args):
    video = Path(args.video).expanduser().resolve(strict=True)
    config = Path(args.samples).expanduser().resolve(strict=True)
    report = Path(args.report).expanduser().resolve()
    require(report.suffix.lower() == '.json', 'Report must be a JSON file')
    require(report not in {video, config}, 'Report must not overwrite video/config')
    samples = json.loads(config.read_text(encoding='utf-8'))
    require(isinstance(samples, list) and samples, 'Samples must be a nonempty list')
    probe = subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate,avg_frame_rate','-of','json',str(video)], text=True)
    stream = json.loads(probe)['streams'][0]
    fps = Fraction(stream['r_frame_rate'])
    require(fps > 0 and Fraction(stream['avg_frame_rate']) == fps, 'Use a verified constant-frame-rate export')
    count = int(stream['nb_frames']) if str(stream.get('nb_frames','')).isdigit() else None
    sha_before = digest(video)
    rows = []
    with tempfile.TemporaryDirectory(prefix='rico-dots-') as folder:
        for index, sample in enumerate(samples):
            require(isinstance(sample, dict), 'Each sample must be an object')
            require(sample.get('roi_reviewed_unobstructed') is True, 'Review ROI as unobstructed first')
            frame = sample.get('frame')
            require(type(frame) is int and frame >= 0, 'Frame must be a nonnegative integer')
            require(count is None or frame < count, 'Frame is outside export')
            require('fps' not in sample or Fraction(str(sample['fps'])) == fps, 'Sample fps differs from actual export')
            roi = sample.get('roi')
            require(isinstance(roi,list) and len(roi)==4 and all(type(v) is int for v in roi), 'ROI must contain four integer pixels')
            x0,y0,x1,y1 = roi
            require(0<=x0<x1<=stream['width'] and 0<=y0<y1<=stream['height'], 'ROI is outside output canvas')
            threshold = sample.get('contrast_threshold')
            minimum = sample.get('minimum_bright_pixels')
            require(type(threshold) in {int,float} and 0<threshold<=255, 'Set contrast threshold from the actual baseline')
            require(type(minimum) is int and minimum>0, 'Set a positive minimum from the actual baseline')
            expected = sample.get('expected_present',True)
            require(type(expected) is bool, 'expected_present must be boolean')
            require(args.regression or expected, 'Release mode cannot expect missing dots')
            target = Path(folder) / f'{index}.png'
            subprocess.run(['ffmpeg','-v','error','-ss',f'{float(frame/fps):.9f}','-i',str(video),'-map','0:v:0','-frames:v','1','-update','1','-y',str(target)], check=True)
            image = Image.open(target).convert('L').crop(tuple(roi))
            blur = image.filter(ImageFilter.GaussianBlur(4))
            bright = sum(int(a)-int(b)>threshold for a,b in zip(image.getdata(),blur.getdata()))
            present = bright >= minimum
            rows.append({**sample,'fps':float(fps),'sharp_bright_pixels':bright,'point_signal_present':present,'matches_expectation':present==expected})
    require(digest(video)==sha_before, 'Video changed while checking; review again')
    matched = all(row['matches_expectation'] for row in rows)
    result = {'schema_version':1,'mode':'regression' if args.regression else 'release','video':{'path':str(video),'sha256':sha_before},'all_match':matched,'samples':rows,'scope':'Reviewed clean ROIs only; not proof of glow, mobile visibility or aesthetic approval'}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'mode':result['mode'],'samples':len(rows),'all_match':matched,'report':str(report)},ensure_ascii=False))
    return 0 if matched else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video',required=True)
    parser.add_argument('--samples',required=True)
    parser.add_argument('--report',required=True)
    parser.add_argument('--regression',action='store_true',help='Allow known missing-dot negative controls; not release approval')
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError,ValueError,KeyError,IndexError,subprocess.SubprocessError) as error:
        print('CHECK NOT PASSED: '+str(error),file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
