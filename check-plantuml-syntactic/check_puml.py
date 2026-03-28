import os
import glob
import urllib.request
import zlib
import base64
import string
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = str.maketrans(base64_alphabet, plantuml_alphabet)

def encode_puml(text):
    zlibbed_str = zlib.compress(text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).decode('utf-8').translate(b64_to_plantuml)

def check_puml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        # 通过分割@startuml和@enduml提取uml代码
        text = f"@startuml\n{text.split('@startuml')[1].split('@enduml')[0]}\n@enduml"
    
    encoded = encode_puml(text)
    url = 'https://www.plantuml.com/plantuml/svg/' + encoded
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return False
        # Treat other errors as False too for now
        return False
    except Exception as e:
        return False
    return False

def main(base_dir):
    systems = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    
    results = []
    
    for system in systems:
        system_dir = os.path.join(base_dir, system)
        puml_files = glob.glob(os.path.join(system_dir, '*.puml'))
        
        # Sort files based on numeric prefix if possible, otherwise string sort
        def sort_key(f):
            basename = os.path.basename(f)
            name_without_ext = os.path.splitext(basename)[0]
            try:
                return int(name_without_ext)
            except ValueError:
                return name_without_ext
                
        puml_files.sort(key=sort_key)
        
        if not puml_files:
            continue
            
        system_results = {'systemname': system}
        passed_count = 0
        
        # Use ThreadPoolExecutor to speed up checking files for a system
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {executor.submit(check_puml, f): f for f in puml_files}
            file_status = {}
            for future in as_completed(future_to_file):
                f = future_to_file[future]
                basename = os.path.basename(f)
                name_without_ext = os.path.splitext(basename)[0]
                try:
                    is_passed = future.result()
                    file_status[f] = is_passed
                except Exception as e:
                    file_status[f] = False
        
        for f in puml_files:
            basename = os.path.basename(f)
            name_without_ext = f"uml{os.path.splitext(basename)[0]}"
            is_passed = file_status[f]
            if is_passed:
                passed_count += 1
                system_results[name_without_ext] = '✅'
            else:
                system_results[name_without_ext] = '❌'
                
        pass_rate = passed_count / len(puml_files)
        system_results['passrate'] = f"{pass_rate:.2f}"
        
        # Keep track of file names for CSV header
        system_results['_files'] = [f"uml{os.path.splitext(os.path.basename(f))[0]}" for f in puml_files]
        
        results.append(system_results)
        print(f"Processed {system}: pass rate {pass_rate:.2f}")

    # Generate CSV
    csv_file = f"{base_dir.split('/')[-1]}_puml_pass_rates.csv"
    
    # Collect all unique uml columns
    all_uml_cols = set()
    for r in results:
        all_uml_cols.update(r['_files'])
        
    # Sort them nicely
    def col_sort_key(c):
        if c.startswith('uml'):
            try:
                return int(c[3:])
            except ValueError:
                return c
        return c
    
    uml_cols_sorted = sorted(list(all_uml_cols), key=col_sort_key)
    
    headers = ['systemname', 'passrate'] + uml_cols_sorted
    
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            row_to_write = {k: v for k, v in r.items() if k != '_files'}
            writer.writerow(row_to_write)
            
    print(f"\nDone! CSV written to {csv_file}")

if __name__ == '__main__':
    path = "/Users/bytedance/Downloads/RQ3/RQ3"
    for i in os.listdir(path):
        print(i)
        if os.path.isdir(os.path.join(path, i)) and (i.startswith('0.6b') or i.startswith('8b')):
            if main(os.path.join(path, i)):
                print(f"{i} pass")
            else:
                print(f"{i} fail")
