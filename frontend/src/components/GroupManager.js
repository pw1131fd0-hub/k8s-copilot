import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import OnlineUsersList from './OnlineUsersList';
import {
  createGroup,
  getGroups,
  updateGroup,
  deleteGroup,
  addGroupMember,
  removeGroupMember,
} from '../utils/api';

export default function GroupManager() {
  const { t } = useTranslation();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [newGroupData, setNewGroupData] = useState({
    name: '',
    description: '',
    visibility: 'private',
  });
  const [newMemberEmail, setNewMemberEmail] = useState('');

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const data = await getGroups();
      setGroups(Array.isArray(data) ? data : data.groups || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupData.name.trim()) {
      setError(t('groupManager.nameRequired') || 'Group name is required');
      return;
    }

    try {
      setLoading(true);
      const group = await createGroup(newGroupData);
      setGroups([...groups, group]);
      setNewGroupData({ name: '', description: '', visibility: 'private' });
      setShowCreateForm(false);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm(t('groupManager.confirmDelete') || 'Delete this group?')) {
      return;
    }

    try {
      await deleteGroup(groupId);
      setGroups(groups.filter(g => g.id !== groupId));
      setSelectedGroup(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAddMember = async () => {
    if (!selectedGroup || !newMemberEmail.trim()) {
      setError(t('groupManager.emailRequired') || 'Email is required');
      return;
    }

    try {
      await addGroupMember(selectedGroup.id, newMemberEmail);
      setNewMemberEmail('');
      // Reload group to update member list
      loadGroups();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!selectedGroup) return;

    if (!window.confirm(t('groupManager.confirmRemove') || 'Remove this member?')) {
      return;
    }

    try {
      await removeGroupMember(selectedGroup.id, userId);
      // Reload groups
      loadGroups();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-100 dark:text-slate-100 mb-6">
        {t('groupManager.title') || 'Collaboration Groups'}
      </h1>

      {error && (
        <div className="mb-4 p-4 bg-red-900 text-red-100 rounded">
          {error}
        </div>
      )}

      {/* Create group button */}
      <button
        onClick={() => setShowCreateForm(!showCreateForm)}
        className="mb-6 px-4 py-2 bg-blue-600 dark:bg-blue-600 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors"
      >
        {t('groupManager.createNew') || '+ Create New Group'}
      </button>

      {/* Create group form */}
      {showCreateForm && (
        <div className="mb-6 p-4 bg-slate-800 dark:bg-slate-800 rounded border border-slate-700 dark:border-slate-700">
          <h2 className="text-lg font-bold text-slate-100 dark:text-slate-100 mb-4">
            {t('groupManager.createForm') || 'Create New Group'}
          </h2>
          <input
            type="text"
            value={newGroupData.name}
            onChange={(e) => setNewGroupData({ ...newGroupData, name: e.target.value })}
            placeholder={t('groupManager.namePlaceholder') || 'Group name'}
            className="w-full mb-4 px-3 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded border border-slate-600 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500"
          />
          <textarea
            value={newGroupData.description}
            onChange={(e) => setNewGroupData({ ...newGroupData, description: e.target.value })}
            placeholder={t('groupManager.descriptionPlaceholder') || 'Group description (optional)'}
            className="w-full mb-4 px-3 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded border border-slate-600 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500 resize-none h-20"
          />
          <select
            value={newGroupData.visibility}
            onChange={(e) => setNewGroupData({ ...newGroupData, visibility: e.target.value })}
            className="w-full mb-4 px-3 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded border border-slate-600 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500"
          >
            <option value="private">{t('groupManager.private') || 'Private'}</option>
            <option value="team">{t('groupManager.team') || 'Team'}</option>
            <option value="public">{t('groupManager.public') || 'Public'}</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={handleCreateGroup}
              disabled={loading}
              className="px-4 py-2 bg-green-600 dark:bg-green-600 text-white rounded hover:bg-green-700 dark:hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {t('groupManager.create') || 'Create'}
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded hover:bg-slate-600 dark:hover:bg-slate-600 transition-colors"
            >
              {t('common.cancel') || 'Cancel'}
            </button>
          </div>
        </div>
      )}

      {/* Groups list and details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Groups sidebar */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-bold text-slate-100 dark:text-slate-100 mb-4">
            {t('groupManager.yourGroups') || 'Your Groups'}
          </h2>
          <div className="space-y-2">
            {groups.length === 0 ? (
              <p className="text-slate-400 dark:text-slate-400 text-sm">
                {t('groupManager.noGroups') || 'No groups yet'}
              </p>
            ) : (
              groups.map(group => (
                <button
                  key={group.id}
                  onClick={() => setSelectedGroup(group)}
                  className={`w-full text-left p-3 rounded transition-colors ${
                    selectedGroup?.id === group.id
                      ? 'bg-blue-600 dark:bg-blue-600 text-white'
                      : 'bg-slate-800 dark:bg-slate-800 text-slate-100 dark:text-slate-100 hover:bg-slate-700 dark:hover:bg-slate-700'
                  }`}
                >
                  <div className="font-semibold">{group.name}</div>
                  <div className="text-xs opacity-75">
                    {group.member_count || 0} {t('groupManager.members') || 'members'}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Group details */}
        {selectedGroup && (
          <div className="lg:col-span-2 p-4 bg-slate-800 dark:bg-slate-800 rounded border border-slate-700 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-100 dark:text-slate-100">
                {selectedGroup.name}
              </h2>
              <button
                onClick={() => handleDeleteGroup(selectedGroup.id)}
                className="p-2 text-slate-400 dark:text-slate-400 hover:text-red-400 dark:hover:text-red-400 transition-colors"
              >
                🗑️
              </button>
            </div>

            {selectedGroup.description && (
              <p className="text-slate-300 dark:text-slate-300 mb-4">{selectedGroup.description}</p>
            )}

            <div className="mb-4">
              <span className="text-sm text-slate-400 dark:text-slate-400">
                {t('groupManager.visibility') || 'Visibility'}:{' '}
              </span>
              <span className="font-semibold text-slate-100 dark:text-slate-100">
                {selectedGroup.visibility}
              </span>
            </div>

            {/* Online Users - Real-time Presence */}
            <div className="mb-6">
              <OnlineUsersList groupId={selectedGroup.id} />
            </div>

            {/* Members section */}
            <div className="mb-6">
              <h3 className="font-bold text-slate-100 dark:text-slate-100 mb-3">
                {t('groupManager.membersSection') || 'Members'}
              </h3>
              <div className="space-y-2 mb-4 max-h-40 overflow-y-auto">
                {selectedGroup.members && selectedGroup.members.length > 0 ? (
                  selectedGroup.members.map(member => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-2 bg-slate-700 dark:bg-slate-700 rounded"
                    >
                      <span className="text-slate-100 dark:text-slate-100">{member.email}</span>
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        className="text-slate-400 dark:text-slate-400 hover:text-red-400 dark:hover:text-red-400 transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 dark:text-slate-400 text-sm">
                    {t('groupManager.noMembers') || 'No members yet'}
                  </p>
                )}
              </div>

              {/* Add member form */}
              <div className="flex gap-2">
                <input
                  type="email"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder={t('groupManager.memberEmailPlaceholder') || 'member@example.com'}
                  className="flex-1 px-3 py-2 bg-slate-700 dark:bg-slate-700 text-slate-100 dark:text-slate-100 rounded border border-slate-600 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500"
                />
                <button
                  onClick={handleAddMember}
                  className="px-4 py-2 bg-green-600 dark:bg-green-600 text-white rounded hover:bg-green-700 dark:hover:bg-green-700 transition-colors"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
