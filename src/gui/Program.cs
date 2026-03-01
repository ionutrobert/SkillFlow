using System;
using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace SkillFlowGUI
{
    public class MainForm : Form
    {
        private Button btnDryRun;
        private Button btnMigrate;
        private Button btnStats;
        private Button btnStatus;
        private Button btnRevert;
        private Button btnOptimize;
        private Button btnOpenVault;
        private Button btnOpenConfig;
        private RichTextBox txtOutput;
        private Label lblStatus;
        private string skillflowPath;
        private string configPath;

        // Regex to strip ANSI escape codes (colors)
        private static readonly Regex AnsiRegex = new Regex(@"\x1b\[[0-9;]*m", RegexOptions.Compiled);

        public MainForm()
        {
            // Determine paths relative to executable
            string exePath = Application.ExecutablePath;
            string exeDir = Path.GetDirectoryName(exePath);
            
            // Check common layouts: portable (cli/setup.py) then repo (src/cli/setup.py)
            string portablePath = Path.Combine(exeDir, "cli", "setup.py");
            string repoPath = Path.Combine(exeDir, "src", "cli", "setup.py");
            
            if (File.Exists(portablePath))
            {
                skillflowPath = portablePath;
            }
            else if (File.Exists(repoPath))
            {
                skillflowPath = repoPath;
            }
            else
            {
                // Fallback to hardcoded dev path for convenience
                skillflowPath = @"C:\Work\SkillFlow\setup.py";
                if (!File.Exists(skillflowPath))
                {
                    MessageBox.Show($"Cannot find setup.py. Expected locations:\n{portablePath}\n{repoPath}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    this.Close();
                    return;
                }
            }
            
            configPath = Path.Combine(Path.GetDirectoryName(skillflowPath), "config", "categories.json");
            if (!File.Exists(configPath))
            {
                configPath = @"C:\Work\SkillFlow\config\categories.json";
            }

            InitializeComponents();
            CheckPrerequisites();
        }

        private void InitializeComponents()
        {
            this.Text = "SkillFlow - Smart Skill Organization";
            this.Size = new System.Drawing.Size(700, 500);
            this.StartPosition = FormStartPosition.CenterScreen;

            // Buttons
            btnDryRun = new Button { Text = "Dry Run", Location = new System.Drawing.Point(20, 20), Width = 100 };
            btnMigrate = new Button { Text = "Migrate", Location = new System.Drawing.Point(130, 20), Width = 100 };
            btnStats = new Button { Text = "Statistics", Location = new System.Drawing.Point(240, 20), Width = 100 };
            btnStatus = new Button { Text = "Health", Location = new System.Drawing.Point(350, 20), Width = 100 };
            btnRevert = new Button { Text = "Revert", Location = new System.Drawing.Point(460, 20), Width = 100 };
            btnOptimize = new Button { Text = "Optimize", Location = new System.Drawing.Point(570, 20), Width = 100 };
            btnOpenVault = new Button { Text = "Open Vault", Location = new System.Drawing.Point(20, 60), Width = 100 };
            btnOpenConfig = new Button { Text = "Open Config", Location = new System.Drawing.Point(130, 60), Width = 100 };

            // Output box - use RichTextBox for better formatting
            txtOutput = new RichTextBox
            {
                Location = new System.Drawing.Point(20, 100),
                Size = new System.Drawing.Size(640, 320),
                Multiline = true,
                ScrollBars = RichTextBoxScrollBars.Vertical,
                ReadOnly = true,
                Font = new System.Drawing.Font("Consolas", 9),
                BackColor = System.Drawing.Color.Black,
                ForeColor = System.Drawing.Color.White
            };

            // Status label
            lblStatus = new Label
            {
                Location = new System.Drawing.Point(20, 430),
                Size = new System.Drawing.Size(640, 30),
                Font = new System.Drawing.Font("Segoe UI", 9, System.Drawing.FontStyle.Bold)
            };

            // Event handlers
            btnDryRun.Click += (s, e) => RunCommand("--dry-run");
            btnMigrate.Click += BtnMigrate_Click;
            btnStats.Click += (s, e) => RunCommand("--stats");
            btnStatus.Click += (s, e) => RunCommand("--status");
            btnRevert.Click += (s, e) => RunCommand("--revert");
            btnOptimize.Click += (s, e) => RunCommand("--optimize");
            btnOpenVault.Click += BtnOpenVault_Click;
            btnOpenConfig.Click += BtnOpenConfig_Click;

            // Add controls
            this.Controls.AddRange(new Control[] { btnDryRun, btnMigrate, btnStats, btnStatus, btnRevert, btnOptimize, btnOpenVault, btnOpenConfig, txtOutput, lblStatus });
        }

          private void CheckPrerequisites()
          {
              if (!File.Exists(skillflowPath))
              {
                  MessageBox.Show($"Error: Cannot find setup.py at:\n{skillflowPath}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                  this.Close();
                  return;
              }

              // Check for bundled Python first
              string bundledPython = Path.Combine(Application.StartupPath, "python", "python.exe");
              
              if (File.Exists(bundledPython))
              {
                  lblStatus.Text = "Ready - Using bundled Python";
              }
              else
              {
                  try
                  {
                      Process.Start("python", "--version")?.WaitForExit();
                      lblStatus.Text = "Ready - Python detected in PATH";
                  }
                  catch
                  {
                      lblStatus.Text = "Warning: Python not found. Install Python or use the portable package.";
                  }
              }
          }

        private void BtnMigrate_Click(object sender, EventArgs e)
        {
            var result = MessageBox.Show(
                "This will MOVE all skills to a hidden vault.\n\nSkills will be removed from OpenCode folder and stored in ~/.opencode-skill-libraries.\n\nDo you want to proceed?",
                "Confirm Migration",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning);

            if (result == DialogResult.Yes)
            {
                RunCommand("");
            }
        }

        private void BtnOpenVault_Click(object sender, EventArgs e)
        {
            try
            {
                // Vault location used by SkillFlow
                string vaultPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".opencode-skill-libraries");
                if (Directory.Exists(vaultPath))
                {
                    Process.Start("explorer.exe", vaultPath);
                }
                else
                {
                    MessageBox.Show("Vault directory not found.\nVault is created after migration.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to open vault: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnOpenConfig_Click(object sender, EventArgs e)
        {
            try
            {
                if (!File.Exists(configPath))
                {
                    MessageBox.Show($"Config file not found at:\n{configPath}", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                Process.Start("notepad.exe", configPath);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to open config: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

         private void RunCommand(string arguments)
         {
             if (!File.Exists(skillflowPath))
             {
                 MessageBox.Show("setup.py not found!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                 return;
             }

             txtOutput.Clear();
             lblStatus.Text = "Running...";

             // Determine which Python to use
             string bundledPython = Path.Combine(Application.StartupPath, "python", "python.exe");
             string pythonExe = "python";
             
             if (File.Exists(bundledPython))
             {
                 pythonExe = $"\"{bundledPython}\"";
             }

             var startInfo = new ProcessStartInfo
             {
                 FileName = pythonExe,
                 Arguments = $"\"{skillflowPath}\" {arguments}",
                 WorkingDirectory = Path.GetDirectoryName(skillflowPath),
                 UseShellExecute = false,
                 RedirectStandardOutput = true,
                 RedirectStandardError = true,
                 CreateNoWindow = true,
                 StandardOutputEncoding = System.Text.Encoding.UTF8,
                 StandardErrorEncoding = System.Text.Encoding.UTF8
             };

            var process = new Process
            {
                StartInfo = startInfo,
                EnableRaisingEvents = true
            };

            process.OutputDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    string cleaned = AnsiRegex.Replace(e.Data, ""); // Strip ANSI codes
                    this.Invoke(new Action(() => txtOutput.AppendText(cleaned + Environment.NewLine)));
                }
            };

            process.ErrorDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    string cleaned = AnsiRegex.Replace(e.Data, "");
                    this.Invoke(new Action(() => txtOutput.AppendText("ERROR: " + cleaned + Environment.NewLine)));
                }
            };

            process.Exited += (s, e) =>
            {
                this.Invoke(new Action(() =>
                {
                    lblStatus.Text = $"Completed (exit code: {process.ExitCode})";
                    // Append banner on completion
                    try
                    {
                        string bannerFile = Path.Combine(Path.GetDirectoryName(skillflowPath), "banner.txt");
                        if (File.Exists(bannerFile))
                        {
                            string banner = File.ReadAllText(bannerFile);
                            txtOutput.AppendText("\r\n" + banner);
                        }
                    }
                    catch { }
                }));
            };

            try
            {
                // Show banner at start
                try
                {
                    string bannerFile = Path.Combine(Path.GetDirectoryName(skillflowPath), "banner.txt");
                    if (File.Exists(bannerFile))
                    {
                        string banner = File.ReadAllText(bannerFile);
                        txtOutput.Text = banner + "\r\n";
                    }
                }
                catch { }

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                lblStatus.Text = "Running...";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to start: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                lblStatus.Text = "Error";
            }
        }
    }

    public class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}