import requests
import json
from openai import OpenAI
import re

def call_deepseek_llm(prompt):
    client = OpenAI(
        api_key="Your_API_KEY", 
        base_url="Your_API_URL"
    )

    system_prompt = """
Extract all polymer-based material systems.

Output the structure of each system using the following JSON format:

{
  "Material Name": <string or null>,  // e.g., "PLA/PCL blend with TiO₂"

  "Base Polymer(s)": {
    "Polymer A": {
      "Name": <string>,   // exact name from text
      "Type": <string>,   // one of: "Homopolymer", "Block copolymer", "Random copolymer", 
                          // "Graft copolymer", "Crosslinked polymer", etc.
      "Role": <string>    // e.g., "Matrix", "Reinforcement", "Compatibilizer", "Plasticizer", "Modifier"
    },
    "Polymer B": {
      "Name": <string>,
      "Type": <string>,
      "Role": <string>
    },
    ...
  } or null,

  "Polymer Structure Type": <"Pure polymer" | "Blend" | "Block copolymer" | "Random copolymer" | 
                             "Graft copolymer" | "Crosslinked" | "Filled composite" | null>,

  "Copolymerized/Blended/Crosslinked/Filled With": <string or list of directly bonded or mixed components, or null>,

  "Other Material(Dopants, Additives or Modifiers)": {
    "Material A": {
      "Name": <string>,   // exact name from text
      "Type": <string>,   // one of: "Inorganic nanoparticle", "Carbon nanomaterial", "Plasticizer", 
                          // "Compatibilizer", "Natural fiber", "Functional additive", 
                          // "Chain extender", "Nucleating agent", etc.
      "Role": <string>    // e.g., "Reinforcement", "Plasticizer", "Compatibilizer", "Modifier", "Dopants"
    },
    ...
  } or null,

  "Component Ratio": {
    "Type": <"wt_percent" | "mass_ratio" | "molar_ratio" | "phr" | "range" | "qualitative" | "unknown">,
    "Components": {
      "<component name>": <number or [number, number]>
    },
    "Original": <string or null>
  },

  "Swelling Ratio": {
    "value": <number | [number, number] | null>,
    "unit": < "%" | string | null>,                      
    "description": <string | null>
  },

  "Glass Transition Temperature": {
    "value": <number | [number, number] | null>,
    "unit": <string | null>,                      // e.g., "°C"
    "description": <string | null>
  },

  "Melting Temperature": {
    "value": <number | [number, number] | null>,
    "unit": <string | null>,                      // e.g., "°C"
    "description": <string | null>
  }
}

Your task includes:

1. **Polymer Structure Type Identification**:
   - Classify based on phrasing in the text:
     - "PLA-b-PCL" → "Block copolymer"
     - "PLA-co-PBS" → "Random copolymer"
     - "PLA/PCL blend" → "Blend"
     - "PLA-g-PEG" → "Graft copolymer"
     - "crosslinked PLA" → "Crosslinked"
     - "PLA with nanoclay" → "Filled composite"
   - Place components like PCL, PEG, TiO₂ under `"Copolymerized/Blended/Crosslinked/Filled With"`.

2. **Base Polymer(s) Identification**:
   - Place all core polymers into `"Base Polymer(s)"` as `"Polymer A"`, `"Polymer B"` etc.
   - For each, extract:
     - `"Name"`: exact name (e.g., "PLA", "PCL")
     - `"Type"`: one of "Homopolymer", "Block copolymer", "Crosslinked polymer", etc.
     - `"Role"`: one of "Matrix", "Reinforcement", "Compatibilizer", "Modifier", etc.

3. **Other Materials Extraction**:
   - Non-polymeric or additive components (e.g., TiO₂, Joncryl, CNT) go under `"Other Material"`.
   - Each should include:
     - `"Name"`: literal string
     - `"Type"`: see controlled vocabulary above
     - `"Role"`: see controlled vocabulary above
   - If no such components, return `null`.

4. **Component Ratio Extraction**:
   - Extract any numeric or qualitative description of composition ratio.
   - Examples:
     - `"PLA:PCL = 70:30"` → `"mass_ratio"`
     - `"20 wt% PEG"` → `"wt_percent"`
     - `"PEG content ranged from 10% to 30%"` → `"range"`

5. **Swelling Ratio Extraction**:
   - Extract quantitative swelling ratios with unit (`%`, etc.)
   - If only qualitative (e.g., "showed high swelling in PBS"), return in `"description"`.

Output rules:
- If only one material system is discussed, return **a single JSON object**.
- If multiple distinct Material systems are discussed, return **a JSON list** of multiple such objects.
- If no valid material or property is found, return the string **"NONE"**.
- Do **not** add any extra text or formatting outside the JSON.
- For missing fields, use **null**.

"""

    try:
        # 发送请求并获取响应
        response = client.chat.completions.create(
            model="DeepSeek-R1-Distill-Qwen-32B",
            # model="DeepSeek-R1-671B", # 671B模型用于深度思考
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.05,  # 设置低温度值
            max_tokens=4960
        )
        
        # 返回 API 响应的内容
        return response.choices[0].message.content

    except Exception as e:
        # 错误处理
        print("🚨 异常发生：", str(e))
        return None

