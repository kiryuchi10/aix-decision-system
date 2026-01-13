import React, { useState, useEffect } from 'react';
import { User, Lock, Bell } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [timezone, setTimezone] = useState('America/Chicago');
  const [denseMode, setDenseMode] = useState(false);

  const handleChangePassword = async () => {
    try {
      // TODO: POST /api/v1/auth/change-password
      alert('Password change (mock)');
      setCurrentPassword('');
      setNewPassword('');
    } catch (error) {
      console.error('Failed to change password:', error);
    }
  };

  const handleSavePreferences = async () => {
    try {
      // TODO: POST /api/v1/profile/preferences
      alert('Preferences saved (mock)');
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <User className="w-8 h-8" />
            Profile
          </h1>
          <p className="text-slate-400 mt-1">Account info, security, and preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Account Card */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <User className="w-5 h-5" />
            Account
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Name</span>
              <span className="font-semibold text-white">{user?.full_name || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Email</span>
              <span className="font-semibold text-white">{user?.email || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Role</span>
              <span className="font-semibold text-cyan-400">{user?.role || 'user'}</span>
            </div>
            <button className="w-full btn-secondary">Edit Profile</button>
          </div>
        </div>

        {/* Security Card */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Lock className="w-5 h-5" />
            Security
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full input-field"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full input-field"
                placeholder="••••••••"
              />
            </div>
            <button
              onClick={handleChangePassword}
              className="w-full btn-primary"
            >
              Update Password
            </button>
            <button className="w-full btn-secondary">Setup 2FA</button>
          </div>
        </div>

        {/* Preferences Card */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Preferences
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Timezone</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full input-field"
              >
                <option value="America/Chicago">America/Chicago</option>
                <option value="America/Los_Angeles">America/Los_Angeles</option>
                <option value="Asia/Seoul">Asia/Seoul</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Dense Mode</div>
                <div className="text-sm text-slate-400">Compact UI layout</div>
              </div>
              <input
                type="checkbox"
                checked={denseMode}
                onChange={(e) => setDenseMode(e.target.checked)}
                className="w-5 h-5"
              />
            </div>
            <button
              onClick={handleSavePreferences}
              className="w-full btn-primary"
            >
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
