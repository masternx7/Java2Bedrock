import os
import json
import shutil
import glob
from jproperties import Properties

optifine = Properties()
i = 0
item_type = ["leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots"]

def write_armor(file, gmdl, layer, i):
	if i == 0:
		type = "helmet"
	elif i == 1:
		type = "chestplate"
	elif i == 2:
		type = "leggings"
	elif i == 3:
		type = "boots"
	ajson = {
		"format_version": "1.10.0",
		"minecraft:attachable": {
			"description": {
				"identifier": f"geyser_custom:{gmdl}.player",
				"item": { f"geyser_custom:{gmdl}": "query.owner_identifier == 'minecraft:player'" },
				"materials": {
					"default": "armor_leather",
					"enchanted": "armor_leather_enchanted"
				},
				"textures": {
					"default": f"textures/armor_layer/{layer}",
					"enchanted": "textures/misc/enchanted_item_glint"
				},
				"geometry": {
					"default": f"geometry.player.armor.{type}"
				},
				"scripts": {
					"parent_setup": "variable.helmet_layer_visible = 0.0;"
				},
				"render_controllers": ["controller.render.armor"]
			}
		}
	}
	with open(file, "w") as f:
		f.write(json.dumps(ajson))

while i < 4:
	try:
		with open(f"pack/assets/minecraft/models/item/{item_type[i]}.json", "r") as f:
			data = json.load(f)
	except:
		i += 1
		continue
	for override in data["overrides"]:
		custom_model_data = override["predicate"]["custom_model_data"]
		model = override["model"]
		namespace = model.split(":")[0]
		item = model.split("/")[-1]
		if item in item_type:
			continue
		else:
			try:
				path = model.split(":")[1]
				optifine_file = f"{namespace}_{item}"
				print(f"Processing item: {item}, namespace: {namespace}, path: {path}")
				print(f"Looking for optifine file: pack/assets/minecraft/optifine/cit/ia_generated_armors/{optifine_file}.properties")
				with open(f"pack/assets/minecraft/optifine/cit/ia_generated_armors/{optifine_file}.properties", "rb") as f:
					optifine.load(f)
					if i == 2:
						layer = optifine.get("texture.leather_layer_2").data.split(".")[0]
					else:
						layer = optifine.get("texture.leather_layer_1").data.split(".")[0]
					print(f"Found armor layer: {layer}")
				
				# ตรวจสอบว่าไฟล์ model มีอยู่หรือไม่
				model_file = f"pack/assets/{namespace}/models/{path}.json"
				if not os.path.exists(model_file):
					print(f"Model file not found: {model_file}")
					continue
				if not os.path.exists("staging/target/rp/textures/armor_layer"):
					os.makedirs("staging/target/rp/textures/armor_layer", exist_ok=True)
				
				# คัดลอก armor layer texture
				layer_source = f"pack/assets/minecraft/optifine/cit/ia_generated_armors/{layer}.png"
				layer_target = f"staging/target/rp/textures/armor_layer/{layer}.png"
				
				if not os.path.exists(layer_target):
					if os.path.exists(layer_source):
						shutil.copy(layer_source, layer_target)
						print(f"Copied armor layer: {layer_source} -> {layer_target}")
					else:
						print(f"Armor layer source not found: {layer_source}")
				with open(f"pack/assets/{namespace}/models/{path}.json", "r") as f :
					model_data = json.load(f)
					print(f"Processing model: {namespace}:{path}")
					
					# ตรวจสอบว่ามี textures หรือไม่
					if "textures" not in model_data:
						print(f"No textures found in model: {namespace}:{path}")
						continue
					
					# ลองหา texture layer1 หรือ layer0
					texture_key = None
					if "layer1" in model_data["textures"]:
						texture_key = "layer1"
					elif "layer0" in model_data["textures"]:
						texture_key = "layer0"
					elif "0" in model_data["textures"]:
						texture_key = "0"
					elif "1" in model_data["textures"]:
						texture_key = "1"
					else:
						# หา texture key แรกที่มี
						texture_keys = list(model_data["textures"].keys())
						if texture_keys:
							texture_key = texture_keys[0]
					
					if not texture_key:
						print(f"No valid texture key found in model: {namespace}:{path}")
						print(f"Available texture keys: {list(model_data['textures'].keys())}")
						continue
					
					texture = model_data["textures"][texture_key]
					print(f"Using texture key '{texture_key}': {texture}")
					
					# แยก namespace และ path ของ texture
					if ":" in texture:
						tex_namespace, tpath = texture.split(":", 1)
					else:
						tex_namespace = namespace
						tpath = texture
					
					# สร้างโฟลเดอร์สำหรับ texture ตามโครงสร้างที่ต้องการ
					texture_dir = f"staging/target/rp/textures/{tex_namespace}/item/ia_auto"
					if not os.path.exists(texture_dir):
						os.makedirs(texture_dir, exist_ok=True)
					
					# คัดลอก texture ไปยังตำแหน่งที่ถูกต้อง
					source_texture = f"pack/assets/{tex_namespace}/textures/{tpath}.png"
					target_texture = f"{texture_dir}/{item}.png"
					
					try:
						if os.path.exists(source_texture):
							shutil.copy(source_texture, target_texture)
							print(f"Copied texture: {source_texture} -> {target_texture}")
						else:
							print(f"Source texture not found: {source_texture}")
							# ลองหาไฟล์ในโฟลเดอร์ armor
							armor_source = f"pack/assets/{tex_namespace}/textures/armor/{tpath}.png"
							if os.path.exists(armor_source):
								shutil.copy(armor_source, target_texture)
								print(f"Copied armor texture: {armor_source} -> {target_texture}")
							else:
								print(f"Armor texture also not found: {armor_source}")
					except Exception as e:
						print(f"Error copying texture: {e}")
						print(f"Source: {source_texture}")
						print(f"Target: {target_texture}")
				afile = glob.glob(f"staging/target/rp/attachables/{namespace}/{path}*.json")
				if not afile:
					print(f"No attachable file found matching: staging/target/rp/attachables/{namespace}/{path}*.json")
					continue
				
				print(f"Found attachable file: {afile[0]}")
				with open(afile[0], "r") as f:
					da = json.load(f)["minecraft:attachable"]
					gmdl = da["description"]["identifier"].split(":")[1]
				pfile = afile[0].replace(".json", ".player.json")
				write_armor(pfile, gmdl, layer, i)
				print(f"Created armor file: {pfile}")
			except Exception as e:
				print(e)
				print("Item not found of ...")
				continue
	i += 1
