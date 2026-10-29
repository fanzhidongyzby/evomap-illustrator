---
name: evomap-illustrator
description: 绘制算法、流程、架构与节点关系图，输出可编辑 SVG 和 PNG。默认是克制的 EvoMap-inspired 白底主题，也可用 JSON 自定义颜色与字体。支持通用几何 spec 和经过验证的快速排序模板；不依赖私人文档或专用设计素材。
metadata:
  version: "1.1.0"
---

# EvoMap Illustrator

让图解释对象、状态和因果关系。默认主题是原创的 EvoMap-inspired 视觉实现，不代表原 VI 手册、Logo 或字体资产的公开授权。

## 选择内容与主题

先明确主体、阅读方向、依赖、分支和输入输出。算法图还需明确算法变体、基准选择、等号归属、递归边界和终止条件；实例中的状态由实际计算产生。

读 [风格原则](references/style-guide.md) 与 [spec API](references/spec-format.md)。通用 JSON spec 可表达流程、架构、组织与算法，不限某个产品或文章。它只渲染明确几何元素，不执行参考资料里的代码。

默认主题在 `references/theme.json`，可用 `--theme custom-theme.json` 合并颜色、字体和几何参数，也可在 spec 的 `theme` 中写覆盖值。主题只接受安全 token 和六位 HEX 颜色。用户主题不修改默认主题；现有脚本省略此参数时仍使用原配色和字体。

如果 `.local/profile.json` 存在，读取本机偏好；它不参与 Git 或资源包，可以指定语言及 `theme_file`。相对主题路径以技能目录为基准。当前用户要求优先，不把本地私人路径或资料写进公开输出。

## 通用可读性

用位置、形状、箭头和直接标签表达关系，不以颜色作为唯一语义。文字、边界和背景应有足够对比度，连线不穿过文字，保留外边距。

优先一张完整主图；内容太密时分页，不通过删除对象或把字号缩小来凑画布。图内保留必要节点/边/状态标签，不默认加宣传式页头页脚；JSON spec 不会自动画可见标题。

主题中的字体只是系统 font-family 列表，不分发字体文件。缺少首选字体时使用 PingFang SC、Noto Sans CJK、Arial 等回退，交付时说明实际替代。品牌 Logo、摄影、字体和其他第三方资产需要独立授权。

EvoMap-inspired 默认 profile 使用白底不透明画布、黑白灰主体和少量蓝绿黄强调；彩色面积宜小于10%。这不是任意论文原图、照片或其他主题的通用配色约束。统计图应按其数据任务选择恰当图表、标签和配色，不能将品牌强调色当作多系列分类调色板。

## 绘制

### 任意图

```bash
python3 -I <skill-dir>/scripts/render.py spec \
  --input figure.json --output-dir illustrations --name figure --scale 2
```

自定义主题：

```bash
python3 -I <skill-dir>/scripts/render.py spec \
  --input figure.json --theme custom-theme.json \
  --output-dir illustrations --name figure --scale 2
```

现成例子见 `templates/node-flow.json` 与 `examples/architecture.json`。不要给每个主题复制渲染器；布局和内容在 spec 中表达。

### 快速排序

```bash
python3 -I <skill-dir>/scripts/render.py quicksort \
  --values 6,3,8,1,7,2,5 --output-dir illustrations \
  --name quicksort --scale 2
```

模板执行 Lomuto 原地分区：`pivot=a[hi]`，左边 `<= pivot`、右边 `> pivot`，递归 `[lo,p-1]` 与 `[p+1,hi]`，`lo>=hi` 返回。展示实际交换、分区树与有序结果；只展示发生跨位置交换的扫描，其余状态可在 trace 中查看。

单页教学实例只接受2—7个整数，每个打印值至多3个字符。重复值、负数可用，复杂输入分页。算法追踪函数本身支持更长输入；模板限制是布局限制，不是算法能力限制。

默认不加可见主标题和装饰性页脚；需要完整教学页时增加 `--teaching-page`。自定义 spec 的 `section` 是内容模块标签，是否使用由图的阅读任务决定。

## 导出与验证

SVG只需Python3.9+标准库。PNG需要本地 `rsvg-convert`：macOS可安装librsvg，Debian/Ubuntu可安装librsvg2-bin。没有工具时可用 `--svg-only`，但必须明确PNG未完成，不自动安装或上传资料到外部服务。

`--scale`只改变PNG像素数：1200×511画布配 `--scale 1` 才得到1200×511，配2则翻倍。检查实际文件头。输出名可用中英文、数字、下划线或连字符，但不能包含路径分隔符；已存在文件拒绝覆盖。

运行 `python3 -I scripts/test_render.py`。核对领域逻辑，再打开最终PNG看字体、碰撞、箭头和裁切；自动测试不能代替视觉或事实审查。算法图核对每一步和trace不变量；主题对比度与颜色面积按所选profile检查。

同时保留PNG与SVG；快速排序另有真实 `.trace.json`。API向后兼容，详见 [README](README.md)；Git更新、测试、推送与同步见 [AGENTS](AGENTS.md)。公开代码和本地偏好分开，不强制覆盖分叉或提交 `.local`。
