from lxml import etree
from lxml.etree import _Element, _ElementTree
import sys
import argparse
from typing import Dict, List
import random
import string
import os

class SCT:

    def __init__(self, root: _ElementTree, root_element: _Element, namespaces: Dict[str, str], filename: str, template = False):
        self.root = root
        self.root_element = root_element
        self.ns = namespaces
        self.updated = False
        self.filename = filename
        self.template = template

    def get_sc(self):
        return self.get_single_element(self.root, "sgraph:Statechart")

    def get_diagram(self):
        return self.get_single_element(self.root, "notation:Diagram")

    def get_edges(self):
        return self.get_all_elements(self.get_diagram(), 'edges')

    def get_vertices(self):
        return self.get_marked_vertices(self.get_sc().getchildren())
    
    def get_single_element(self, root: _ElementTree, elem_name:str) -> _Element:
        return root.find(elem_name, self.ns)

    def get_all_elements(self, root: _Element, elem_name:str) -> List[_Element]:
        return root.findall(elem_name, self.ns)
    
    def get_all_vertices_ids(self):
        return self.root.xpath('//*[@xmi:id]/@xmi:id', namespaces=self.ns)

    def get_all_vertrice_region_ids(self, elem: _Element):
        _ids = elem.xpath('.//regions/@xmi:id', namespaces=self.ns)
        _ids.extend(elem.xpath('.//regions//*[@xmi:id]/@xmi:id', namespaces=self.ns))
        return _ids

    def get_all_ids(self):
        _ids = self.root.xpath('.//*/@xmi:id', namespaces=self.ns)
        return set(_ids)

    def pre_process(self):
        ids = self.get_all_ids()
        d = {}
        for id_ in ids:
            d[id_] = '_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=22))
        return d

    def clean_vertrice(self, elem: _Element):
        elem.attrib['specification'] = ''
        _ids = self.get_all_vertrice_region_ids(elem)
        _del = self.get_elements_with_id(_ids)
        for x in _del:
            x.getparent().remove(x)

    def get_elements_with_id(self, _ids):
        _out = []
        elements = self.root.xpath(f"//*")
        for x in elements:
            attrib = x.xpath(f"./@*")
            if any(item in attrib for item in _ids):
                _out.append(x)
        return _out
    
    def get_marked_vertices(self, elem: List[_Element]) -> List[_Element]:
        
        if len(elem) == 0:
            return []

        out = []
        
        child = elem[0]
        name = child.attrib.get('name')
        tag = child.tag
        if (self.template):
            if name != None and tag == "vertices" and len(name) > 1 and name[0] == '_' and name[-1] == '_':
                out.append(child)
        else:
            if name != None and tag == "vertices" and len(name) > 1 and name == f'_{self.filename}_':
                out.append(child)

        out.extend(self.get_marked_vertices(child.getchildren()))
        out.extend(self.get_marked_vertices(elem[1:]))
        return out

    def get_vertices_id(self):
        d = {}
        for x in self.get_vertices():
            d[x.xpath('@name', namespaces=self.ns)[0]] = x.xpath('@xmi:id', namespaces=self.ns)[0]
        return d

    def inject_elements(self, elems: List[_Element]):
        paths = {}
        for elem in elems:
            root = elem.getroottree()
            paths[root.getpath(elem)] = elem
        sec_p = paths.copy()
        
        for x in paths.keys():
            for y in paths.keys():
                if x != y and x in y:
                    if sec_p.get(y) != None:
                        sec_p.pop(y)
        
        name = ""
        for key, value in sec_p.items():
            if ('regions') in key:
                name = value.getparent().attrib.get("name")
                break
        
        _id = self.get_vertices_id().get(name)

        for key, value in sec_p.items():
            if('regions') in key:
                par = self.get_sc().xpath(f".//regions/vertices[@xmi:id='{_id}']", namespaces=self.ns)[0]
                par.append(value)
            if ('edges' in key):
                self.get_diagram().append(value)
            elif ('children' in key):
                par: _Element = self.get_diagram().xpath(f".//*/children[@element='{_id}']/children[@type='StateFigureCompartment']")[0]
                par.append(value)
                

class IO:

    @staticmethod
    def read(path: str) -> _ElementTree:
        return etree.parse(path, None)
    
    @staticmethod
    def write(out: str, tree: _ElementTree):
        out_str = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf-8') # type: ignore
        out_str = out_str.replace('&#10;', '&#xA;').replace('&#9;', '&#x9;').replace('&gt;', '>')
        with open(out, 'w') as f:
            f.write(out_str)
    
    @staticmethod
    def pre_process(read_f: str, replace_dict):
        with open(read_f, 'r') as f:
            data = f.read()
            for key, value in replace_dict.items():
                data = data.replace(key, value)
        
        return etree.fromstring(bytes(data, 'utf-8'))


def run(args):
    template = sct_generator(args.template, True)
    d_map = template.pre_process()
    template = sct_genetaror_from_etree(IO.pre_process(args.template, d_map), args.template)
    
    sources = [sct_generator(x, False) for x in args.sources]

    for vertrice in template.get_vertices():
        template.clean_vertrice(vertrice)
    
    inject(sources, template)
    IO.write(args.out or args.template, template.root)
    
    print("Success!")

def inject(sources: List[SCT], target: SCT):
    target_dict = {vetri.attrib.get("name"): vetri for  vetri in target.get_vertices()}
    for source in sources:
        for vertrice in source.get_vertices():
            if vertrice.attrib.get("name") in target_dict:
                target_elem = target_dict[vertrice.attrib.get("name")]
                target_elem.attrib['specification'] = vertrice.attrib.get('specification') or ''
                _ids = source.get_all_vertrice_region_ids(vertrice)
                _inject = source.get_elements_with_id(_ids)
                target.inject_elements(_inject)

def sct_generator(path:str, template) -> SCT:
    filename = os.path.basename(path).split('.')[0]
    
    try:
        root: _ElementTree = IO.read(path)
    except OSError as e:
        print(type(e))
        sys.exit(1)
    
    root_element: _Element =  root.getroot()
    nsmap: dict[str, str] = {k:v for k,v in root_element.nsmap.items() if k}

    return SCT(root, root_element, nsmap, filename, template)

def sct_genetaror_from_etree(root: _Element, path: str):
    filename = os.path.basename(path).split('.')[0]
    nsmap: dict[str, str] = {k:v for k,v in root.nsmap.items() if k}

    return SCT(root, root, nsmap, filename, True)
    
def main():
    parser = argparse.ArgumentParser(
                    prog = 'yakmerge',
                    description = """
                    split statecharts into components
                    """)
    parser.add_argument("-t", "--template", help='Special statechart file for positioning of the elements', required=True)
    parser.add_argument("-o", "--out", help='Yakindu statechart file')
    parser.add_argument("sources", nargs="+", help='list of glob patterns of input files')
    
    run(parser.parse_args())