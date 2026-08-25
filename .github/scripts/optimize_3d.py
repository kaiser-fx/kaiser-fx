import os
import glob
import re
import xml.etree.ElementTree as ET

ET.register_namespace('', 'http://www.w3.org/2000/svg')

def optimize_svg(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 1. Remove radar and donut charts if present
        for child in list(root):
            tr = child.attrib.get('transform', '')
            if 'translate(980' in tr or 'translate(40, 520)' in tr or 'translate(40,520)' in tr:
                root.remove(child)

        # 2. Straighten grid
        grid = None
        for child in root:
            if child.tag.endswith('g') and len(child) > 50:
                grid = child
                break
                
        if grid is None:
            return

        new_coords = []
        dy_unit = 11.547
        
        for cell in grid:
            tr = cell.attrib.get('transform', '')
            m = re.search(r'translate\(([\d\.]+)\s+([\d\.]+)\)', tr)
            if m:
                x, y = float(m.group(1)), float(m.group(2))
                u = x / 20.0
                v = y / dy_unit
                w = (u + v) / 2.0
                d = (v - u) / 2.0
                
                # Straighten coordinates: gentler slope for week axis
                new_x = w * 21.5 - d * 18.0
                new_y = w * 4.2 + d * 10.4
                new_coords.append((new_x, new_y, cell))

        if not new_coords:
            return

        min_x = min(x for x, y, _ in new_coords)
        min_y = min(y for x, y, _ in new_coords)
        
        margin_x = 40.0
        margin_y = 50.0
        
        for nx, ny, cell in new_coords:
            adj_x = round(nx - min_x + margin_x, 2)
            adj_y = round(ny - min_y + margin_y, 2)
            cell.attrib['transform'] = f'translate({adj_x} {adj_y})'

        max_y = max(round(ny - min_y + margin_y, 2) for nx, ny, _ in new_coords) + 80
        total_w = 1280
        total_h = int(max_y)

        root.attrib['width'] = str(total_w)
        root.attrib['height'] = str(total_h)
        root.attrib['viewBox'] = f'0 0 {total_w} {total_h}'
        
        for child in root:
            if child.tag.endswith('rect') and child.attrib.get('class') == 'fill-bg':
                child.attrib['width'] = str(total_w)
                child.attrib['height'] = str(total_h)

        # Reposition bottom statistics line
        for child in root:
            if child.tag.endswith('g') and len(child) <= 10 and child != grid:
                for el in child:
                    if 'y' in el.attrib:
                        try:
                            if float(el.attrib['y']) > 400:
                                el.attrib['y'] = str(total_h - 25)
                        except ValueError:
                            pass

        tree.write(file_path)
        print(f"Successfully optimized: {file_path}")
    except Exception as e:
        print(f"Error optimizing {file_path}: {e}")

if __name__ == '__main__':
    svg_files = glob.glob('profile-3d-contrib/*.svg')
    for svg_file in svg_files:
        optimize_svg(svg_file)
