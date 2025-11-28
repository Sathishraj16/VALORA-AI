'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Database,
  Cpu,
  Globe,
  Key,
  Save,
  RefreshCw,
  Check,
  AlertTriangle,
  Moon,
  Sun,
  Monitor,
  Zap,
  Activity,
  HardDrive,
} from 'lucide-react';
import { useTheme } from 'next-themes';

interface SettingsSection {
  id: string;
  label: string;
  icon: typeof Settings;
}

const SECTIONS: SettingsSection[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'simulation', label: 'Simulation', icon: Cpu },
  { id: 'api', label: 'API Keys', icon: Key },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'data', label: 'Data Management', icon: Database },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const { theme, setTheme } = useTheme();

  // Form states
  const [profile, setProfile] = useState({
    name: 'Dr. Sarah Chen',
    email: 'sarah.chen@valora.ai',
    organization: 'Economic Research Institute',
    role: 'Senior Economist',
    timezone: 'Asia/Kolkata',
  });

  const [notifications, setNotifications] = useState({
    simulationComplete: true,
    policyAlerts: true,
    agentAnomalies: true,
    weeklyReports: false,
    emailNotifications: true,
    pushNotifications: false,
  });

  const [simulationSettings, setSimulationSettings] = useState({
    defaultSteps: 1000,
    autoSave: true,
    autoSaveInterval: 100,
    parallelAgents: 10000,
    gpuAcceleration: true,
    cachingEnabled: true,
    logLevel: 'info',
  });

  const [apiKeys, setApiKeys] = useState({
    groq: '••••••••••••••••••••',
    openai: '',
    anthropic: '',
  });

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="flex gap-6 h-full">
      {/* Sidebar */}
      <div className="w-64 shrink-0">
        <div className="glass-card p-4 sticky top-0">
          <h2 className="text-lg font-semibold mb-4">Settings</h2>
          <nav className="space-y-1">
            {SECTIONS.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary/20 text-primary'
                    : 'hover:bg-white/5'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <span>{section.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-6">
        {/* Profile Section */}
        {activeSection === 'profile' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                Profile Information
              </h3>

              <div className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-6">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-3xl font-bold">
                    SC
                  </div>
                  <div>
                    <button className="btn-secondary mb-2">Change Avatar</button>
                    <p className="text-sm text-muted-foreground">
                      JPG, PNG or GIF. Max 2MB.
                    </p>
                  </div>
                </div>

                {/* Form Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Full Name</label>
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Email</label>
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Organization</label>
                    <input
                      type="text"
                      value={profile.organization}
                      onChange={(e) =>
                        setProfile({ ...profile, organization: e.target.value })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Role</label>
                    <input
                      type="text"
                      value={profile.role}
                      onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium mb-2">Timezone</label>
                    <select
                      value={profile.timezone}
                      onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                      <option value="America/New_York">America/New_York (EST)</option>
                      <option value="Europe/London">Europe/London (GMT)</option>
                      <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Appearance Section */}
        {activeSection === 'appearance' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Palette className="w-5 h-5 text-primary" />
                Appearance
              </h3>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-4">Theme</label>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { id: 'light', label: 'Light', icon: Sun },
                      { id: 'dark', label: 'Dark', icon: Moon },
                      { id: 'system', label: 'System', icon: Monitor },
                    ].map((option) => (
                      <button
                        key={option.id}
                        onClick={() => setTheme(option.id)}
                        className={`p-4 rounded-xl border-2 transition-colors ${
                          theme === option.id
                            ? 'border-primary bg-primary/10'
                            : 'border-white/10 hover:border-white/20'
                        }`}
                      >
                        <option.icon className="w-6 h-6 mx-auto mb-2" />
                        <p className="text-sm font-medium">{option.label}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-4">Accent Color</label>
                  <div className="flex gap-3">
                    {['#6366f1', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b'].map(
                      (color) => (
                        <button
                          key={color}
                          className="w-10 h-10 rounded-full border-2 border-white/20 transition-transform hover:scale-110"
                          style={{ backgroundColor: color }}
                        />
                      )
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Chart Animation Speed</label>
                  <input
                    type="range"
                    min="0"
                    max="2000"
                    step="100"
                    defaultValue="500"
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Instant</span>
                    <span>Slow</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Notifications Section */}
        {activeSection === 'notifications' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Bell className="w-5 h-5 text-primary" />
                Notification Preferences
              </h3>

              <div className="space-y-4">
                {[
                  {
                    key: 'simulationComplete',
                    label: 'Simulation Complete',
                    description: 'Get notified when a simulation finishes running',
                  },
                  {
                    key: 'policyAlerts',
                    label: 'Policy Alerts',
                    description: 'Receive alerts about significant policy impacts',
                  },
                  {
                    key: 'agentAnomalies',
                    label: 'Agent Anomalies',
                    description: 'Get notified about unusual agent behavior patterns',
                  },
                  {
                    key: 'weeklyReports',
                    label: 'Weekly Reports',
                    description: 'Receive weekly summary reports via email',
                  },
                ].map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between p-4 bg-white/5 rounded-xl"
                  >
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-muted-foreground">{item.description}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifications[item.key as keyof typeof notifications]}
                        onChange={(e) =>
                          setNotifications({
                            ...notifications,
                            [item.key]: e.target.checked,
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-white/10 peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t border-white/10">
                <h4 className="font-medium mb-4">Delivery Methods</h4>
                <div className="flex gap-4">
                  <label className="flex items-center gap-3 p-4 bg-white/5 rounded-xl cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.emailNotifications}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          emailNotifications: e.target.checked,
                        })
                      }
                      className="w-5 h-5 accent-primary"
                    />
                    <span>Email</span>
                  </label>
                  <label className="flex items-center gap-3 p-4 bg-white/5 rounded-xl cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.pushNotifications}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          pushNotifications: e.target.checked,
                        })
                      }
                      className="w-5 h-5 accent-primary"
                    />
                    <span>Push Notifications</span>
                  </label>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Simulation Section */}
        {activeSection === 'simulation' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                Simulation Settings
              </h3>

              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Default Simulation Steps
                    </label>
                    <input
                      type="number"
                      value={simulationSettings.defaultSteps}
                      onChange={(e) =>
                        setSimulationSettings({
                          ...simulationSettings,
                          defaultSteps: parseInt(e.target.value),
                        })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Max Parallel Agents
                    </label>
                    <input
                      type="number"
                      value={simulationSettings.parallelAgents}
                      onChange={(e) =>
                        setSimulationSettings({
                          ...simulationSettings,
                          parallelAgents: parseInt(e.target.value),
                        })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Auto-save Interval (steps)
                    </label>
                    <input
                      type="number"
                      value={simulationSettings.autoSaveInterval}
                      onChange={(e) =>
                        setSimulationSettings({
                          ...simulationSettings,
                          autoSaveInterval: parseInt(e.target.value),
                        })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Log Level</label>
                    <select
                      value={simulationSettings.logLevel}
                      onChange={(e) =>
                        setSimulationSettings({
                          ...simulationSettings,
                          logLevel: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="debug">Debug</option>
                      <option value="info">Info</option>
                      <option value="warning">Warning</option>
                      <option value="error">Error</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  {[
                    {
                      key: 'autoSave',
                      label: 'Auto-save Simulations',
                      description: 'Automatically save simulation state periodically',
                      icon: HardDrive,
                    },
                    {
                      key: 'gpuAcceleration',
                      label: 'GPU Acceleration',
                      description: 'Use GPU for faster agent computations',
                      icon: Zap,
                    },
                    {
                      key: 'cachingEnabled',
                      label: 'Enable Caching',
                      description: 'Cache intermediate results for faster replays',
                      icon: Activity,
                    },
                  ].map((item) => (
                    <div
                      key={item.key}
                      className="flex items-center justify-between p-4 bg-white/5 rounded-xl"
                    >
                      <div className="flex items-center gap-3">
                        <item.icon className="w-5 h-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{item.label}</p>
                          <p className="text-sm text-muted-foreground">{item.description}</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={
                            simulationSettings[item.key as keyof typeof simulationSettings] as boolean
                          }
                          onChange={(e) =>
                            setSimulationSettings({
                              ...simulationSettings,
                              [item.key]: e.target.checked,
                            })
                          }
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-white/10 peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* API Keys Section */}
        {activeSection === 'api' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Key className="w-5 h-5 text-primary" />
                API Keys
              </h3>

              <div className="space-y-6">
                {[
                  {
                    key: 'groq',
                    label: 'Groq API Key',
                    description: 'Required for AI-powered policy analysis',
                    status: 'configured',
                  },
                  {
                    key: 'openai',
                    label: 'OpenAI API Key',
                    description: 'Optional - for GPT-4 based analysis',
                    status: 'not_configured',
                  },
                  {
                    key: 'anthropic',
                    label: 'Anthropic API Key',
                    description: 'Optional - for Claude-based analysis',
                    status: 'not_configured',
                  },
                ].map((item) => (
                  <div key={item.key} className="p-4 bg-white/5 rounded-xl">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-medium">{item.label}</p>
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          item.status === 'configured'
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}
                      >
                        {item.status === 'configured' ? 'Configured' : 'Not Configured'}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        value={apiKeys[item.key as keyof typeof apiKeys]}
                        onChange={(e) =>
                          setApiKeys({ ...apiKeys, [item.key]: e.target.value })
                        }
                        placeholder="Enter API key..."
                        className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                      />
                      <button className="btn-secondary">Verify</button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-500">Security Notice</p>
                    <p className="text-sm text-muted-foreground">
                      API keys are encrypted and stored securely. Never share your API keys
                      with anyone.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Security Section */}
        {activeSection === 'security' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Shield className="w-5 h-5 text-primary" />
                Security Settings
              </h3>

              <div className="space-y-6">
                <div>
                  <h4 className="font-medium mb-4">Change Password</h4>
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">New Password</label>
                      <input
                        type="password"
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <button className="btn-primary">Update Password</button>
                  </div>
                </div>

                <div className="pt-6 border-t border-white/10">
                  <h4 className="font-medium mb-4">Two-Factor Authentication</h4>
                  <div className="p-4 bg-white/5 rounded-xl">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">2FA Status</p>
                        <p className="text-sm text-muted-foreground">
                          Add an extra layer of security to your account
                        </p>
                      </div>
                      <button className="btn-secondary">Enable 2FA</button>
                    </div>
                  </div>
                </div>

                <div className="pt-6 border-t border-white/10">
                  <h4 className="font-medium mb-4">Sessions</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                      <div className="flex items-center gap-3">
                        <Monitor className="w-5 h-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">Current Session</p>
                          <p className="text-sm text-muted-foreground">
                            Mumbai, India • Chrome on Windows
                          </p>
                        </div>
                      </div>
                      <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">
                        Active
                      </span>
                    </div>
                    <button className="text-red-400 text-sm hover:underline">
                      Sign out of all other sessions
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Data Management Section */}
        {activeSection === 'data' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Database className="w-5 h-5 text-primary" />
                Data Management
              </h3>

              <div className="space-y-6">
                <div className="p-4 bg-white/5 rounded-xl">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="font-medium">Storage Usage</p>
                      <p className="text-sm text-muted-foreground">2.4 GB of 10 GB used</p>
                    </div>
                    <span className="text-2xl font-bold">24%</span>
                  </div>
                  <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-purple-500 rounded-full"
                      style={{ width: '24%' }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-white/5 rounded-xl">
                    <p className="font-medium mb-2">Export All Data</p>
                    <p className="text-sm text-muted-foreground mb-4">
                      Download all your simulations and settings
                    </p>
                    <button className="btn-secondary w-full">Export Data</button>
                  </div>
                  <div className="p-4 bg-white/5 rounded-xl">
                    <p className="font-medium mb-2">Clear Cache</p>
                    <p className="text-sm text-muted-foreground mb-4">
                      Free up storage by clearing cached data
                    </p>
                    <button className="btn-secondary w-full">Clear Cache</button>
                  </div>
                </div>

                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <p className="font-medium text-red-400 mb-2">Danger Zone</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Permanently delete all your data. This action cannot be undone.
                  </p>
                  <button className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors">
                    Delete All Data
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Save Button */}
        <div className="flex items-center justify-end gap-4 pt-6 border-t border-white/10">
          {saveSuccess && (
            <motion.span
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-green-400"
            >
              <Check className="w-5 h-5" />
              Settings saved successfully
            </motion.span>
          )}
          <button className="btn-secondary">Cancel</button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
