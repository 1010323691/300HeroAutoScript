// 300HeroAuto.exe —— 一键启动器：启动 toolkit\WebApp 里的 Electron 桌面壳
// 编译: csc /target:winexe /r:System.Windows.Forms.dll /out:300HeroAuto.exe Launcher.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("300英雄 自动脚本")]
[assembly: AssemblyProduct("300HeroAutoScript")]
[assembly: AssemblyVersion("1.1.0.0")]

static class Launcher
{
    const string Title = "300英雄 自动脚本";

    [STAThread]
    static int Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string ui = Path.Combine(root, @"toolkit\WebApp\300HeroAutoUI.exe");
        string py = Path.Combine(root, @"toolkit\python\python.exe");

        if (!File.Exists(ui) || !File.Exists(py))
        {
            string tmp = Path.GetTempPath();
            string hint = root.StartsWith(tmp, StringComparison.OrdinalIgnoreCase)
                ? "看起来你是在压缩包里直接双击的。\n请先把压缩包【全部解压】到一个文件夹，再双击里面的 300HeroAuto.exe。"
                : "程序文件不完整（缺少 toolkit 文件夹）。\n请重新完整解压压缩包，不要只复制 exe。";
            MessageBox.Show(hint + "\n\n当前位置：" + root, Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }

        try
        {
            var psi = new ProcessStartInfo(ui)
            {
                WorkingDirectory = Path.GetDirectoryName(ui),
                UseShellExecute = false,
            };
            psi.EnvironmentVariables["APP_ROOT"] = root.TrimEnd('\\');
            Process.Start(psi);
            return 0;
        }
        catch (Exception e)
        {
            MessageBox.Show("启动失败：" + e.Message, Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 2;
        }
    }
}
