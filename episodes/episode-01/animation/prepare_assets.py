#!/usr/bin/env python3
"""Extract reusable animation layers from Teo's immutable approved pixels.

No painting, generative fill, inpainting, or redesign. RGB is copied verbatim.
Alpha masks, crops, and pivots are production derivatives, never new masters.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
OUT = BASE / "rig-assets"
SPECS = {
    "2d": {
        "threshold": 25,
        "floor_y": 1380,
        "shoes": [
            [(334,1327),(391,1332),(406,1355),(409,1385),(414,1414),(419,1458),(407,1469),(343,1483),(298,1490),(263,1489),(240,1482),(239,1466),(243,1449),(260,1436),(286,1418),(308,1380),(319,1346)],
            [(600,1344),(656,1344),(674,1359),(680,1394),(683,1417),(701,1440),(716,1462),(722,1493),(717,1508),(682,1515),(645,1511),(611,1500),(594,1484),(592,1462),(596,1400)],
        ],
        "head_poly": [(290,0),(640,0),(640,215),(575,234),(554,259),(501,280),(451,279),(443,258),(455,243),(453,215),(381,182),(324,155)],
        "head_pivot": [492,258],
        "neck_pivot": [493,264],
        "hip_y": 756,
        "crotch": [466,825],
        "knee_y": 1050,
        "hips": {"left": [397,773], "right": [551,773]},
        "knees": {"left": [391,1058], "right": [593,1068]},
        "ankles": {"left": [365,1330], "right": [634,1350]},
        "arm_polys": {
            "left": [(300,299),(348,298),(357,350),(371,410),(388,440),(390,483),(379,524),(372,548),(372,595),(359,640),(350,678),(362,697),(331,729),(317,755),(300,722),(278,607),(273,540),(303,466)],
            "right": [(657,277),(707,294),(740,385),(746,453),(755,554),(725,615),(683,679),(641,747),(619,758),(604,720),(581,700),(598,674),(619,621),(628,569),(650,527),(626,492),(613,449),(605,414),(614,342)]
        },
        "shoulders": {"left": [354,332], "right": [664,332]},
        "elbows": {"left": [331,548], "right": [685,536]},
        "wrists": {"left": [328,696], "right": [616,707]},
        "face_rect": [399,91,557,223],
        "mouth_rect": [434,162,503,193],
        "mouth_center": [468,179],
        "eye_centers": [[431,135],[484,123]],
    },
    "3d": {
        "threshold": 25,
        "floor_y": 1380,
        "shoes": [
            [(337,1312),(388,1314),(407,1335),(411,1364),(413,1391),(423,1427),(420,1445),(402,1453),(359,1460),(308,1463),(274,1458),(258,1451),(260,1426),(270,1407),(291,1394),(308,1363),(323,1338)],
            [(591,1320),(644,1323),(662,1344),(669,1384),(678,1408),(693,1435),(698,1457),(693,1471),(672,1479),(633,1477),(610,1470),(597,1457),(587,1442),(584,1410),(585,1367)],
        ],
        "head_poly": [(320,36),(622,36),(622,219),(565,241),(555,274),(531,294),(491,317),(461,309),(452,286),(451,264),(406,243),(360,207),(322,164)],
        "head_pivot": [494,292],
        "neck_pivot": [495,298],
        "hip_y": 763,
        "crotch": [468,821],
        "knee_y": 1068,
        "hips": {"left": [399,776], "right": [549,776]},
        "knees": {"left": [391,1068], "right": [586,1070]},
        "ankles": {"left": [370,1313], "right": [621,1330]},
        "arm_polys": {
            "left": [(321,351),(358,328),(371,348),(375,398),(390,451),(396,490),(390,529),(380,554),(380,599),(364,649),(360,683),(364,699),(344,731),(330,756),(310,729),(289,608),(289,558),(314,482)],
            "right": [(647,317),(683,326),(711,395),(723,447),(730,502),(735,565),(715,612),(678,664),(640,720),(620,762),(597,767),(579,720),(571,703),(590,681),(611,627),(629,582),(647,543),(630,517),(613,481),(605,448),(603,412),(610,351)]
        },
        "shoulders": {"left": [354,366], "right": [660,370]},
        "elbows": {"left": [337,559], "right": [683,552]},
        "wrists": {"left": [339,703], "right": [607,714]},
        "face_rect": [404,139,557,267],
        "mouth_rect": [436,207,502,238],
        "mouth_center": [466,222],
        "eye_centers": [[434,181],[486,170]],
    },
}


def poly(points, size=(1024,1536)):
    im = Image.new("L", size)
    ImageDraw.Draw(im).polygon(points, fill=255)
    return np.asarray(im)>0


def segment(rgb, spec):
    # Estimate the original cream backdrop independently on each scanline.
    l = np.median(rgb[:,8:130].astype(float), axis=1)
    r = np.median(rgb[:,894:1016].astype(float), axis=1)
    x = np.linspace(0,1,rgb.shape[1])[None,:,None]
    bg = l[:,None,:]*(1-x)+r[:,None,:]*x
    dist = np.linalg.norm(rgb.astype(float)-bg, axis=2)
    mask = dist > spec["threshold"]
    # The original soft floor shadow is not character art.
    feet = np.zeros(mask.shape,dtype=bool)
    for p in spec["shoes"]:
        feet |= poly(p)
    mask[spec["floor_y"]:] &= feet[spec["floor_y"]:]
    labels,n = ndi.label(mask)
    sizes = np.bincount(labels.ravel()); sizes[0]=0
    mask = labels == sizes.argmax()
    # Retain intentional gaps between arms and torso / between legs.
    holes = ndi.binary_fill_holes(mask)&~mask
    hl,hn=ndi.label(holes)
    hs=np.bincount(hl.ravel()); hs[0]=10**9
    mask |= hs[hl] < 70
    # Light shoe details must be solid inside their true outer boundary.
    for p in spec["shoes"]:
        region=poly(p)
        mask |= ndi.binary_fill_holes(mask&region)&region
    # A single-pixel alpha ramp keeps edges clean without altering RGB.
    # Outside RGB remains source background but has zero alpha.
    inside=ndi.distance_transform_edt(mask)
    alpha=np.where(mask,np.minimum(1,inside/1.1)*255,0).astype(np.uint8)
    return alpha


def rgba(rgb,alpha):
    return Image.fromarray(np.dstack([rgb,alpha]),"RGBA")


def checker(im):
    h,w=np.asarray(im).shape[:2]
    y,x=np.indices((h,w))
    a=np.where(((x//24+y//24)%2)[...,None],205,239)
    bg=np.broadcast_to(a,(h,w,3)).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(bg,"RGB").convert("RGBA"),im).convert("RGB")


def save_layer(rgb, alpha, name, output, pivot, parent=None):
    im=rgba(rgb,alpha)
    im.save(output/f"{name}.png")
    Image.fromarray(alpha,"L").save(output/f"{name}-mask.png")
    bbox=im.getbbox()
    if bbox:
        im.crop(bbox).save(output/f"{name}-crop.png")
    return {"file":f"{name}.png","mask":f"{name}-mask.png", "crop":f"{name}-crop.png", "bbox":bbox,"pivot":pivot,"crop_pivot":[pivot[0]-bbox[0],pivot[1]-bbox[1]] if bbox else None,"parent":parent,"rest":{"translation":[0,0],"rotation_degrees":0,"scale":[1,1]}}


def main():
    OUT.mkdir(exist_ok=True)
    manifest={"canvas":[1024,1536],"coordinate_system":"source image pixels; origin top-left; positive x right, positive y down; left/right names are viewer-left/viewer-right","rgb_policy":"Every layer RGB is copied exactly from approved source; only alpha masks differ. No redraw or inpainting.","styles":{}}
    for style,spec in SPECS.items():
        source=REPO/"characters/teo/images"/f"teo-approved-{style}.png"
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        rgb=np.asarray(Image.open(source).convert("RGB"))
        alpha=segment(rgb,spec)
        d=OUT/style;d.mkdir(exist_ok=True)
        full=rgba(rgb,alpha);full.save(d/"teo-cutout.png")
        Image.fromarray(alpha).save(d/"character-alpha.png")
        checker(full).save(d/"cutout-checkerboard.png")
        # Exact disjoint rest-pose partition; no holes when stacked unchanged.
        y,x=np.indices(alpha.shape)
        head=poly(spec["head_poly"])
        hips=spec["hip_y"]
        legs=(y>=hips)
        split_x=spec["crotch"][0]
        # Split joggers at the central seam until the actual crotch gap begins.
        left_leg=legs&(x<split_x)
        right_leg=legs&~left_leg
        left_arm=poly(spec["arm_polys"]["left"])&~head&~legs
        right_arm=poly(spec["arm_polys"]["right"])&~head&~legs&~left_arm
        torso=~(head|legs|left_arm|right_arm)
        masks={"head":head,"torso":torso,"arm-left":left_arm,"arm-right":right_arm,"leg-left":left_leg,"leg-right":right_leg}
        layers={}
        for name,mask in masks.items():
            if name=="head":p=spec["head_pivot"];parent="torso"
            elif name=="torso":p=[480,hips];parent=None
            elif name.startswith("arm"):p=spec["shoulders"][name.split("-")[1]];parent="torso"
            else:p=spec["hips"][name.split("-")[1]];parent="torso"
            layers[name]=save_layer(rgb,np.where(mask,alpha,0).astype(np.uint8),name,d,p,parent)
        # Overlap copies are optional for bending; do not stack all variants.
        # They contain existing pixels only. Keep rotation small to avoid gaps.
        ky=spec["knee_y"]
        for side,lmask in [("left",left_leg),("right",right_leg)]:
            for part,mask in [("upper",lmask&(y<ky+24)),("lower",lmask&(y>=ky-24))]:
                pivot=spec["hips"][side] if part=="upper" else spec["knees"][side]
                name=f"leg-{side}-{part}"
                layers[name]=save_layer(rgb,np.where(mask,alpha,0).astype(np.uint8),name,d,pivot,"torso" if part=="upper" else f"leg-{side}-upper")
        upper_body=(y<hips)
        layers["upper-body"]=save_layer(rgb,np.where(upper_body,alpha,0).astype(np.uint8),"upper-body",d,[480,hips],None)
        # Overlap at the waist can hide tiny separations during gentle sway.
        layers["upper-body-overlap"]=save_layer(rgb,np.where(y<hips+26,alpha,0).astype(np.uint8),"upper-body-overlap",d,[480,hips],None)
        layers["upper-body-no-head"]=save_layer(rgb,np.where((y<hips+26)&~head,alpha,0).astype(np.uint8),"upper-body-no-head",d,[480,hips],None)
        face=np.zeros(alpha.shape,dtype=bool);a,b,c,e=spec["face_rect"];face[b:e,a:c]=True
        layers["face-original"]=save_layer(rgb,np.where(face,alpha,0).astype(np.uint8),"face-original",d,spec["mouth_center"],"head")
        # Verify the default 6 disjoint layers recreate the full cutout exactly.
        summed=np.zeros(alpha.shape,dtype=np.uint16)
        for mask in masks.values():summed+=np.where(mask,alpha,0).astype(np.uint16)
        assert np.array_equal(summed,alpha),"rest-pose partition does not reconstruct alpha"
        assert hashlib.sha256(source.read_bytes()).hexdigest()==before
        info={"source":str(source),"source_sha256":before,"canvas":[1024,1536],"cutout":"teo-cutout.png","alpha":"character-alpha.png","rest_partition":["leg-left","leg-right","torso","arm-left","arm-right","head"],"gentle_walk_layers":["leg-left-lower","leg-right-lower","leg-left-upper","leg-right-upper","upper-body-overlap"],"layers":layers,"landmarks":{k:spec[k] for k in ["head_pivot","neck_pivot","hips","knees","ankles","shoulders","elbows","wrists","mouth_rect","mouth_center","eye_centers"]},"limitations":["Artwork is one fixed three-quarter view with hands in pockets, not a full 3D character rig.","No hidden body parts were synthesized; large rotations/strides can expose gaps or alter the apparent silhouette.","Use gentle leg articulation and weight shifts, keep arms with torso for natural hands-in-pockets pose.","Use whole upper-body for gap-free rests; upper-body overlap covers waist seams during small motions.","Do not overlay the face-original layer unchanged when head moves; it is a source patch for matching facial deformation."]}
        (d/"rig.json").write_text(json.dumps(info,indent=2)+"\n")
        manifest["styles"][style]={"directory":style,"rig":f"{style}/rig.json","source_sha256":before,"rest_partition_verified":True}
        print(style, "alpha bounds", full.getbbox(), "opaque",int(np.count_nonzero(alpha)),"source",before)
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


if __name__=="__main__":
    main()
