// JnoSig —— 在 Juno: New Origins 主菜单版本号后追加汉化署名
// 原理: 定位 MainMenu 里 xmlLayout.GetElementById<TextMeshProUGUI>("version-number-text").text = ...
//       在其 set_text 调用前插入 IL:  ldstr "<后缀>"  +  string::Concat(string,string)
// 特性: 幂等（重复运行不会重复插入）、自动备份原 dll
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

internal static class Program
{
    private const string Marker = "LyuRinYu汉化";
    private const string Suffix = "  ·  LyuRinYu汉化";   // 追加在版本号后面

    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("用法: JnoSig <SimpleRockets2.dll 路径> [--write]");
            return 1;
        }
        var path = args[0];
        var write = args.Contains("--write");
        if (!File.Exists(path)) { Console.WriteLine("找不到文件: " + path); return 1; }

        // 立即读取模式 + 内存读取：避免写回时再回头解析已关闭的文件流
        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(path)));
        var asm = AssemblyDefinition.ReadAssembly(path, new ReaderParameters
        {
            InMemory = true,
            ReadingMode = ReadingMode.Immediate,
            ReadSymbols = false,
            AssemblyResolver = resolver,
        });
        int added = 0, existed = 0;

        foreach (var type in AllTypes(asm.MainModule))
        {
            foreach (var method in type.Methods)
            {
                if (!method.HasBody) continue;
                var il = method.Body.GetILProcessor();
                var ins = method.Body.Instructions;

                for (int i = 0; i < ins.Count; i++)
                {
                    if (ins[i].OpCode != OpCodes.Ldstr) continue;
                    if (!(ins[i].Operand is string lit) || lit != "version-number-text") continue;

                    // 往后找第一个 set_text 调用（即 .text = <值> 的赋值点）
                    for (int j = i + 1; j < ins.Count; j++)
                    {
                        var op = ins[j];
                        var isCall = op.OpCode == OpCodes.Callvirt || op.OpCode == OpCodes.Call;
                        if (!isCall || !(op.Operand is MethodReference mr) || mr.Name != "set_text") continue;

                        // 幂等检查：set_text 之前几条里是否已有我们的后缀
                        var dup = false;
                        for (int k = Math.Max(0, j - 5); k < j; k++)
                            if (ins[k].OpCode == OpCodes.Ldstr && ins[k].Operand is string s && s.Contains(Marker))
                                dup = true;
                        if (dup) { existed++; break; }

                        var strType = asm.MainModule.TypeSystem.String;
                        var concat = new MethodReference("Concat", strType, strType) { HasThis = false };
                        concat.Parameters.Add(new ParameterDefinition(strType));
                        concat.Parameters.Add(new ParameterDefinition(strType));

                        var ldstrInst = il.Create(OpCodes.Ldstr, Suffix);
                        var callInst = il.Create(OpCodes.Call, asm.MainModule.ImportReference(concat));
                        il.InsertBefore(op, ldstrInst);
                        il.InsertBefore(op, callInst);
                        added++;
                        Console.WriteLine($"[命中] {type.FullName}.{method.Name}  -> 已插入后缀 \"{Suffix}\"");
                        break;
                    }
                }
            }
        }

        Console.WriteLine($"\n补丁点: 新增 {added} 处, 已存在 {existed} 处");
        if (added == 0 && existed == 0)
        {
            Console.WriteLine("未找到目标代码，dll 可能版本不符（方法名: version-number-text / set_text）");
            return 2;
        }
        if (!write)
        {
            Console.WriteLine("(预览模式，加 --write 保存修改)");
            return 0;
        }
        if (added == 0) { Console.WriteLine("无需写入。"); return 0; }

        var bak = path + ".orig";
        if (!File.Exists(bak))
        {
            File.Copy(path, bak);
            Console.WriteLine($"已备份原 dll -> {bak}");
        }
        // 关键: 绝不直接写原路径 —— Cecil 的 Write 会先截断目标文件，
        // 一旦中途失败原 dll 就变成 0 字节（会造成游戏无法启动）。
        // 因此先写临时文件，回读校验有效后再覆盖。
        var tmp = path + ".patched";
        asm.Write(tmp);
        asm.Dispose();
        try
        {
            using (var chk = AssemblyDefinition.ReadAssembly(tmp, new ReaderParameters { ReadSymbols = false }))
            {
                if (chk.MainModule.Types.Count == 0) throw new Exception("类型数为 0");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"补丁文件校验失败，已保留原 dll 未替换: {ex.Message}");
            File.Delete(tmp);
            return 3;
        }
        var size = new FileInfo(tmp).Length;
        File.Copy(tmp, path, true);
        File.Delete(tmp);
        Console.WriteLine($"已写入 {path}  ({size} 字节, 校验通过)");
        return 0;
    }

    private static IEnumerable<TypeDefinition> AllTypes(ModuleDefinition m)
    {
        foreach (var t in m.Types)
        {
            yield return t;
            foreach (var n in Nested(t)) yield return n;
        }
    }

    private static IEnumerable<TypeDefinition> Nested(TypeDefinition t)
    {
        foreach (var n in t.NestedTypes)
        {
            yield return n;
            foreach (var x in Nested(n)) yield return x;
        }
    }
}
