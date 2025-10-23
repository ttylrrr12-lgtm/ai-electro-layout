import argparse, os, sys, subprocess

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='yolo11n.pt')
    p.add_argument('--epochs', type=int, default=50)
    p.add_argument('--img', type=int, default=1024)
    p.add_argument('--data', default='dataset.yaml')
    args = p.parse_args()
    cmd = [
        sys.executable, '-m', 'ultralytics', 'train',
        f'model={args.model}', f'data={args.data}', f'epochs={args.epochs}', f'imgsz={args.img}'
    ]
    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)

if __name__ == '__main__':
    main()
