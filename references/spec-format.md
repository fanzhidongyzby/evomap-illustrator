# 通用插图 JSON spec

`render.py spec`将JSON布局渲染为SVG和PNG。坐标以逻辑像素计，`--scale 2`只增加PNG分辨率，不改变布局。颜色使用主题token；`--theme file.json`或spec中的`theme`可覆盖默认颜色、字体与几何参数，不需要修改全局主题。元素的fill/stroke仍引用token，不直接执行任意SVG或CSS。

```json
{
  "width": 1200,
  "height": 700,
  "title": "图的可访问性标题",
  "description": "不依赖颜色的文字描述",
  "elements": [
    {"type": "text", "x": 64, "y": 112, "value": "节点与连接", "size": 44, "weight": 600},
    {"type": "rect", "x": 400, "y": 240, "w": 220, "h": 80},
    {"type": "text", "x": 510, "y": 288, "value": "主体", "align": "middle"},
    {"type": "arrow", "points": [[510,320], [510,390], [310,390], [310,460]]}
  ]
}
```

## 元素 API

元素顺序就是绘制顺序。通常先画连接，再画节点和文字；连接不要穿过文字。SVG 会自动加入标题、描述、箭头 marker 和整张白色背景。

| type | 必填 | 可选 |
|---|---|---|
| text | x, y, value | size=20, weight=400, color=ink, align=start/middle/end, font=body/latin/code |
| rect | x, y, w, h | fill=paper, stroke=line, radius=14, sw=1.5 |
| circle | x, y, r | fill=paper, stroke=none, sw=1.5 |
| line | x1, y1, x2, y2 | color=line, sw=1.5 |
| path | d（SVG 路径） | fill=none, stroke=secondary, sw=2, arrow=false |
| arrow | points（二维坐标列表） | color=secondary, sw=2；转折自动圆角 |
| array | x, y, values | cell=62, gap=9, pivot=null（数组内下标）, active=[]（交换下标）, size=30, indices=false, pivot_marker=true |
| section | x, y, number, title | subtitle=null；小蓝条、编号、标题 |

`text.y` 是基线，`rect` 和 `array` 的 `(x,y)` 是左上角。文字是安全转义后的文本，不能嵌入原始 SVG、HTML、脚本或外部资源。长文字需要拆为多个 `text` 元素；不会隐式换行。箭头大小是固定的小尺寸，不随线宽变粗。

`array` 中 `pivot` 使用黄底 + 深色边界 + 小三角，`active` 使用小面积浅蓝和蓝色底条，其余单元格为中性灰。每个元素都保留深色值标签，因此去掉颜色也可以阅读。

## 运行与复用

```bash
python3 .claude/skills/evomap-illustrator/scripts/render.py spec \
  --input .claude/skills/evomap-illustrator/templates/node-flow.json \
  --output-dir illustrations --name node-flow-evomap --scale 2
```

新图只需新增spec。默认白底；自定义主题的`paper`决定画布填色。不要重复添加全画布背景，也不要把装饰性色块当作主要信息结构。

主题覆盖示例：

```json
{"colors":{"ink":"#1F2937","blue":"#2563EB"},"fonts":{"body":"Noto Sans CJK SC, Arial, sans-serif"}}
```

通过`--theme theme.json`传入，或把对象放在spec的`theme`字段。覆盖值合并默认主题，互不污染。输出名支持中英文，但不接受路径分隔符、目录跳转或超过180字节的名字。

## 布局验收

- 标签、数字、箭头和外边距必须完整；白底不能遮盖内容。
- 主流程 / 主要关系使用深灰线；颜色点缀不是唯一关系标识。
- 在最终 PNG 中核验中文字体、基线、文字宽度和色彩面积。
- 通用渲染器只执行 spec，不验证图所表达的领域事实。必须另外核验算法、技术架构或业务逻辑。
