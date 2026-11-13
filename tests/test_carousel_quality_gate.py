import copy
import struct
import unittest
from carousel_quality_gate import validate_contract, apply_slide_patch, release_gate, png_dimensions, PNG_HEADER

def fixture():
    return {"brand":"Paulina Gubelin Walker","post_id":"S02_P03","topic":"rebaja",
            "editorial_revision":"v1","visual_revision":"v1",
            "approved_slide_count":3,
            "slides":[{"id":str(i).zfill(2),"topic":"rebaja","headline":"Titular "+str(i),
                       "purpose":"Función "+str(i)} for i in range(1,4)]}

class CarouselQualityGateTests(unittest.TestCase):
    def setUp(self):self.c=fixture()
    def test_valid(self):self.assertEqual(validate_contract(self.c),[])
    def test_count_change_blocks(self):
        self.c["approved_slide_count"]=5
        self.assertTrue(validate_contract(self.c))
    def test_cross_topic_blocks(self):
        self.c["slides"][1]["topic"]="cobro"
        self.assertTrue(validate_contract(self.c))
    def test_order_blocks(self):
        self.c["slides"][1]["id"]="03"
        self.assertTrue(validate_contract(self.c))
    def test_targeted_patch_only_modifies_one(self):
        old=copy.deepcopy(self.c)
        new=apply_slide_patch(self.c,"02",{"body":"Nueva redacción"},"v1")
        self.assertEqual(new["slides"][0],old["slides"][0])
        self.assertEqual(new["slides"][2],old["slides"][2])
        self.assertEqual(old["slides"][1],self.c["slides"][1])
        self.assertEqual(new["slides"][1]["body"],"Nueva redacción")
    def test_stale_revision_blocks(self):
        with self.assertRaises(ValueError):
            apply_slide_patch(self.c,"02",{"body":"X"},"v0")
    def test_unauthorized_patch_blocks(self):
        with self.assertRaises(ValueError):
            apply_slide_patch(self.c,"02",{"topic":"incumplimiento"},"v1")
    def test_no_publish_without_approvals(self):
        a=[{"slide_id":s["id"],"size":[1080,1350],"sha256":s["id"]} for s in self.c["slides"]]
        self.assertEqual(release_gate(self.c,a)["status"],"BLOQUEADO")
    def test_happy_structural_gate(self):
        a=[{"slide_id":s["id"],"size":[1080,1350],"sha256":s["id"]} for s in self.c["slides"]]
        sources={s["id"]:{"native":True} for s in self.c["slides"]}
        approvals={k:True for k in ("art","legal","brand","publication")}
        self.assertEqual(release_gate(self.c,a,sources,approvals)["status"],"APTO_ESTRUCTURAL")
    def test_wrong_size_blocks(self):
        a=[{"slide_id":s["id"],"size":[1080,1350],"sha256":s["id"]} for s in self.c["slides"]]
        a[0]["size"]=[1024,1024]
        self.assertEqual(release_gate(self.c,a)["status"],"BLOQUEADO")
    def test_png_dimensions_parser(self):
        fake=PNG_HEADER+b"\x00\x00\x00\x0dIHDR"+struct.pack(">II",1080,1350)
        self.assertEqual(png_dimensions(fake),(1080,1350))
    def test_reject_invalid_png(self):
        with self.assertRaises(ValueError):png_dimensions(b"not an image")

if __name__=="__main__":unittest.main()
