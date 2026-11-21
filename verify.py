import os
import sys
import subprocess
import tempfile
import hashlib

def get_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def verify_png(path):
    if not os.path.exists(path):
        print(f"Error: {path} does not exist")
        return False
    size = os.path.getsize(path)
    if size > 1048576:
        print(f"Error: {path} size {size} exceeds 1,048,576 bytes")
        return False
    with open(path, 'rb') as f:
        header = f.read(24)
    if not header.startswith(b'\x89PNG\r\n\x1a\n'):
        print(f"Error: {path} has invalid PNG signature")
        return False
    if header[12:16] != b'IHDR':
        print(f"Error: {path} IHDR chunk not found at expected offset")
        return False
    width = int.from_bytes(header[16:20], 'big')
    height = int.from_bytes(header[20:24], 'big')
    if width != 1024 or height != 1024:
        print(f"Error: {path} dimensions are {width}x{height}, expected 1024x1024")
        return False
    return True

def main():
    print("Verifying entry.png...")
    if not verify_png('entry.png'):
        sys.exit(1)

    print("Re-rendering to check determinism...")
    with tempfile.TemporaryDirectory() as tmpdir:
        sub1 = os.path.join(tmpdir, 'sub1')
        sub2 = os.path.join(tmpdir, 'sub2')
        os.makedirs(sub1)
        os.makedirs(sub2)

        for sub in [sub1, sub2]:
            with open('render.py', 'rb') as sf:
                code = sf.read()
            with open(os.path.join(sub, 'render.py'), 'wb') as df:
                df.write(code)
            if os.path.exists('stories.py'):
                with open('stories.py', 'rb') as sf:
                    scode = sf.read()
                with open(os.path.join(sub, 'stories.py'), 'wb') as df:
                    df.write(scode)

        subprocess.run([sys.executable, 'render.py'], cwd=sub1, check=True, capture_output=True)
        subprocess.run([sys.executable, 'render.py'], cwd=sub2, check=True, capture_output=True)

        p1 = os.path.join(sub1, 'entry.png')
        p2 = os.path.join(sub2, 'entry.png')

        if not verify_png(p1) or not verify_png(p2):
            print("Error: re-rendered PNGs failed validation")
            sys.exit(1)

        sha1 = get_sha256(p1)
        sha2 = get_sha256(p2)
        if sha1 != sha2:
            print("Error: re-rendered PNGs are not byte-identical")
            sys.exit(1)

    import render
    cards = getattr(render, 'CARDS', None)
    briefs = getattr(render, 'BRIEFS', None)

    if cards is None or briefs is None:
        print("Error: CARDS or BRIEFS not found in render module")
        sys.exit(1)

    if len(cards) != 20:
        print(f"Error: expected 20 cards, got {len(cards)}")
        sys.exit(1)
    if len(briefs) != 50:
        print(f"Error: expected 50 briefs, got {len(briefs)}")
        sys.exit(1)

    total_stories = len(cards) + len(briefs)
    if total_stories != 70:
        print(f"Error: total stories {total_stories} != 70")
        sys.exit(1)

    # Per-region counts from brief: EUROPE 20, THE AMERICAS 15, ASIA-PACIFIC 13, MIDDLE EAST 7, AFRICA 9, OCEANIA 3, WORLD 3 = 70
    region_counts = [20, 15, 13, 7, 9, 3, 3]
    if sum(region_counts) != 70:
        print(f"Error: region counts sum to {sum(region_counts)}, expected 70")
        sys.exit(1)

    print("Testing main.ts from foreign working directory...")
    if not os.path.exists('main.ts'):
        print("Error: main.ts does not exist")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as foreign_dir:
        with open('main.ts', 'rb') as f:
            mcode = f.read()
        with open(os.path.join(foreign_dir, 'main.ts'), 'wb') as f:
            f.write(mcode)

        with open('entry.png', 'rb') as f:
            pcode = f.read()
        with open(os.path.join(foreign_dir, 'entry.png'), 'wb') as f:
            f.write(pcode)

        out_dir = os.path.join(foreign_dir, 'out_test')
        env = os.environ.copy()
        env['MAKEFUN_OUTPUT_DIR'] = out_dir

        res = subprocess.run(['node', 'main.ts'], cwd=foreign_dir, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error: main.ts exited with code {res.returncode}")
            print("STDOUT:", res.stdout)
            print("STDERR:", res.stderr)
            sys.exit(1)

        copied_png = os.path.join(out_dir, 'entry.png')
        if not os.path.exists(copied_png):
            print(f"Error: main.ts did not copy entry.png to {copied_png}")
            sys.exit(1)

        if get_sha256(copied_png) != get_sha256('entry.png'):
            print("Error: copied entry.png is not byte-identical to original")
            sys.exit(1)

    print("ALL CHECKS PASSED")

if __name__ == '__main__':
    main()
