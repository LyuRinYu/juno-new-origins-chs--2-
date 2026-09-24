# dll-patch

在游戏主菜单的版本号后面追加汉化署名的 Mono.Cecil 补丁工具。

## 它改了什么

游戏主菜单脚本里有这样一行：

```csharp
xmlLayout.GetElementById<TextMeshProUGUI>("version-number-text").text
    = string.Format("v" + Game.Instance.VersionWithSuffix);
```

本工具在 `set_text` 调用之前插入两条 IL 指令，把结果拼上后缀：

```
IL: ... call string::Format(string, object[])
IL:     ldstr "  ·  LyuRinYu汉化"      <- 插入
IL:     call string::Concat(string,string)   <- 插入
IL:     callvirt TMP_Text::set_text
```

IL 栈平衡保持不变（此时栈上正是待赋值的文本），因此不会破坏原逻辑。

## 安全设计

- 找不到 `version-number-text` / `set_text` 补丁点 → **报错退出，不写文件**
- 幂等：检测到已打过补丁则跳过
- 写入前自动备份 `.orig`
- 写入临时文件 → 回读校验 → 才覆盖原文件（避免截断风险）

## 依赖

- Mono.Cecil 0.11.5（MIT），已随包提供于 `../scripts/lib/`
- .NET SDK 10（编译用）

## 用法

```bash
dotnet build -c Release
bin/Release/net10.0/JnoSig.exe "<游戏目录>/SimpleRockets2_Data/Managed/SimpleRockets2.dll"           # 预览
bin/Release/net10.0/JnoSig.exe "<游戏目录>/SimpleRockets2_Data/Managed/SimpleRockets2.dll" --write   # 写入
```

还原：`python ../scripts/restore_dll.py`
