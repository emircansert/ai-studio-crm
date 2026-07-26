"use client";

import { RefreshCw, ShieldCheck, UserPlus } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { SectionAccessDefinition, SectionAccessLevel, User, UserAccessMatrixResponse, UserSectionAccessResponse } from "@/types/api";

type UserForm = {
  email: string;
  full_name: string;
  role: "ADMIN" | "USER";
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({ email: "", full_name: "", role: "USER", is_active: true });
  const [form, setForm] = useState<UserForm>({
    email: "",
    full_name: "",
    role: "USER"
  });
  const [sectionDefinitions, setSectionDefinitions] = useState<SectionAccessDefinition[]>([]);
  const [accessRows, setAccessRows] = useState<UserAccessMatrixResponse["users"]>([]);
  const [accessDraft, setAccessDraft] = useState<Record<string, Record<string, SectionAccessLevel>>>({});
  const [savingAccessByUser, setSavingAccessByUser] = useState<Record<string, boolean>>({});

  const filteredUsers = useMemo(() => users, [users]);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (role) params.set("role", role);
      if (status) params.set("is_active", status);
      params.set("limit", "500");
      const [usersResponse, accessResponse] = await Promise.all([
        apiRequest<User[]>(`/api/v1/admin/users?${params.toString()}`),
        apiRequest<UserAccessMatrixResponse>(`/api/v1/admin/users/section-access?${params.toString()}`)
      ]);
      setUsers(usersResponse);
      setSectionDefinitions(accessResponse.sections);
      setAccessRows(accessResponse.users);
      setAccessDraft(
        accessResponse.users.reduce<Record<string, Record<string, SectionAccessLevel>>>((acc, row) => {
          acc[row.user.id] = row.access;
          return acc;
        }, {})
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load users");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    try {
      await apiRequest<User>("/api/v1/admin/users", {
        method: "POST",
        body: JSON.stringify(form)
      });
      setNotice("User created. They sign in with their Microsoft account.");
      setForm({ email: "", full_name: "", role: "USER" });
      setCreateOpen(false);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create user");
    }
  }

  async function updateUser(userId: string, payload: Record<string, unknown>, message: string) {
    setError(null);
    setNotice(null);
    try {
      await apiRequest<User>(`/api/v1/admin/users/${userId}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      setNotice(message);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update user");
    }
  }

  function openEdit(user: User) {
    setEditingUser(user);
    setEditForm({
      email: user.email,
      full_name: user.full_name,
      role: user.role === "ADMIN" ? "ADMIN" : "USER",
      is_active: user.is_active
    });
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingUser) return;
    await updateUser(editingUser.id, editForm, "User profile updated.");
    setEditingUser(null);
  }

  async function patchUser(userId: string, path: string, payload: Record<string, unknown> | null, message: string) {
    setError(null);
    setNotice(null);
    try {
      await apiRequest<User>(`/api/v1/admin/users/${userId}/${path}`, {
        method: "PATCH",
        body: payload ? JSON.stringify(payload) : undefined
      });
      setNotice(message);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update user");
    }
  }

  async function saveSectionAccess(userId: string) {
    setSavingAccessByUser((value) => ({ ...value, [userId]: true }));
    setError(null);
    setNotice(null);
    try {
      const response = await apiRequest<UserSectionAccessResponse>(`/api/v1/admin/users/${userId}/section-access`, {
        method: "PUT",
        body: JSON.stringify({ access: accessDraft[userId] ?? {} })
      });
      setAccessDraft((value) => ({ ...value, [userId]: response.access }));
      setNotice("Section access updated.");
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update section access");
    } finally {
      setSavingAccessByUser((value) => ({ ...value, [userId]: false }));
    }
  }

  function setDraftAccess(userId: string, sectionKey: string, accessLevel: SectionAccessLevel) {
    setAccessDraft((value) => ({
      ...value,
      [userId]: {
        ...(value[userId] ?? {}),
        [sectionKey]: accessLevel
      }
    }));
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="User Management"
        description="Pre-provision Entra users, manage roles and section access, and deactivate accounts."
        actions={
          <div className="button-row">
            <Button variant="secondary" onClick={() => void load()}>
              <RefreshCw size={16} />
              Refresh
            </Button>
            <Button onClick={() => setCreateOpen((value) => !value)}>
              <UserPlus size={16} />
              Create User
            </Button>
          </div>
        }
      />

      <div className="command-hero">
        <div>
          <h2>Entra ID identity management</h2>
          <p>
            Sign-in is handled entirely by Microsoft Entra ID; the CRM stores no passwords. Users are created
            automatically on first sign-in, are retained and deactivated rather than deleted, and the only active admin
            is protected from accidental lockout.
          </p>
        </div>
        <Badge tone="info">{isLoading ? "Loading" : `${users.length} users`}</Badge>
      </div>

      <SectionCard>
        <form
          className="crm-toolbar"
          onSubmit={(event) => {
            event.preventDefault();
            void load();
          }}
        >
          <Input placeholder="Search name or email" value={q} onChange={(event) => setQ(event.target.value)} />
          <Select aria-label="Role" value={role} onChange={(event) => setRole(event.target.value)}>
            <option value="">Any role</option>
            <option value="ADMIN">Admin</option>
            <option value="USER">User</option>
          </Select>
          <Select aria-label="Status" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">Any status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </Select>
          <Button type="submit">Apply filters</Button>
        </form>
        {notice ? <div className="alert alert--success">{notice}</div> : null}
        {error ? <div className="alert alert--error">{error}</div> : null}
      </SectionCard>

      {createOpen ? (
        <SectionCard>
          <div className="section-heading">
            <h2>Create user</h2>
            <p>
              Optional: pre-provision a record so a role and section access can be set before the person&apos;s first
              sign-in. Use their Entra sign-in address (UPN). No password is set &mdash; they authenticate with their
              Microsoft account, and a record is created automatically on first sign-in either way.
            </p>
          </div>
          <form className="form-stack" onSubmit={createUser}>
            <div className="two-column">
              <Input required label="Email (Entra UPN)" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
              <Input required label="Full name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
              <Select label="Role" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as UserForm["role"] })}>
                <option value="USER">User</option>
                <option value="ADMIN">Admin</option>
              </Select>
            </div>
            <Button type="submit">
              <ShieldCheck size={16} />
              Create user
            </Button>
          </form>
        </SectionCard>
      ) : null}

      {editingUser ? (
        <SectionCard>
          <div className="section-heading section-heading--inline">
            <div>
              <h2>Edit user</h2>
              <p>Update the CRM copy of the user&apos;s identity details, role, and active state.</p>
            </div>
            <Button variant="ghost" onClick={() => setEditingUser(null)}>Cancel</Button>
          </div>
          <form className="form-stack" onSubmit={saveEdit}>
            <div className="two-column">
              <Input required label="Email" type="email" value={editForm.email} onChange={(event) => setEditForm({ ...editForm, email: event.target.value })} />
              <Input required label="Full name" value={editForm.full_name} onChange={(event) => setEditForm({ ...editForm, full_name: event.target.value })} />
              <Select label="Role" value={editForm.role} onChange={(event) => setEditForm({ ...editForm, role: event.target.value })}>
                <option value="USER">User</option>
                <option value="ADMIN">Admin</option>
              </Select>
              <Select label="Status" value={String(editForm.is_active)} onChange={(event) => setEditForm({ ...editForm, is_active: event.target.value === "true" })}>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </Select>
            </div>
            <Button type="submit">Save user</Button>
          </form>
        </SectionCard>
      ) : null}

      <SectionCard>
        <div className="section-heading">
          <h2>Users</h2>
          <p>Admin-only. Identities come from Microsoft Entra ID; roles and active state are managed here.</p>
        </div>
        <Table
          rows={filteredUsers}
          getRowKey={(row) => row.id}
          columns={[
            {
              key: "user",
              header: "User",
              render: (row) => (
                <div className="record-title">
                  <strong>{row.full_name}</strong>
                  <span className="record-subtitle">{row.email}</span>
                </div>
              )
            },
            { key: "role", header: "Role", render: (row) => <Badge tone={row.role === "ADMIN" ? "info" : "neutral"}>{row.role}</Badge> },
            { key: "active", header: "Status", render: (row) => <Badge tone={row.is_active ? "success" : "danger"}>{row.is_active ? "ACTIVE" : "INACTIVE"}</Badge> },
            { key: "login", header: "Last login", render: (row) => formatDate(row.last_login_at) },
            {
              key: "roleAction",
              header: "Change role",
              render: (row) => (
                <Select
                  aria-label={`Role for ${row.email}`}
                  value={row.role}
                  onChange={(event) => void patchUser(row.id, "role", { role: event.target.value }, "Role updated.")}
                >
                  <option value="USER">User</option>
                  <option value="ADMIN">Admin</option>
                </Select>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="button-row">
                  <Button
                    variant={row.is_active ? "danger" : "secondary"}
                    onClick={() => void patchUser(row.id, row.is_active ? "deactivate" : "activate", null, row.is_active ? "User deactivated." : "User activated.")}
                  >
                    {row.is_active ? "Deactivate" : "Activate"}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => openEdit(row)}
                  >
                    Edit
                  </Button>
                </div>
              )
            }
          ]}
        />
      </SectionCard>

      <SectionCard>
        <div className="section-heading">
          <h2>Section access matrix</h2>
          <p>
            Set each user&apos;s sidebar section access. Hidden removes the section and blocks its API, View-only allows read
            endpoints, and Full access allows create/edit/archive actions. User Management remains admin-only outside this matrix.
          </p>
        </div>
        <div className="alert alert--warning">
          New USER accounts default to Hidden for controlled sections until an admin grants access. New ADMIN accounts default to Full.
        </div>
        <div className="table-wrap">
          <table className="data-table access-matrix">
            <thead>
              <tr>
                <th>User</th>
                {sectionDefinitions.map((section) => (
                  <th key={section.key}>{section.label}</th>
                ))}
                <th>Save</th>
              </tr>
            </thead>
            <tbody>
              {accessRows.map((row) => (
                <tr key={row.user.id}>
                  <td>
                    <div className="record-title">
                      <strong>{row.user.full_name}</strong>
                      <span className="record-subtitle">{row.user.email}</span>
                    </div>
                  </td>
                  {sectionDefinitions.map((section) => (
                    <td key={section.key}>
                      <Select
                        aria-label={`${section.label} access for ${row.user.email}`}
                        className="access-cell-select"
                        value={accessDraft[row.user.id]?.[section.key] ?? "HIDDEN"}
                        onChange={(event) => setDraftAccess(row.user.id, section.key, event.target.value as SectionAccessLevel)}
                      >
                        <option value="HIDDEN">Hidden</option>
                        <option value="VIEW">View-only</option>
                        <option value="FULL">Full access</option>
                      </Select>
                    </td>
                  ))}
                  <td>
                    <Button
                      variant="secondary"
                      disabled={savingAccessByUser[row.user.id]}
                      onClick={() => void saveSectionAccess(row.user.id)}
                    >
                      {savingAccessByUser[row.user.id] ? "Saving" : "Save"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!accessRows.length ? <div className="empty-state">No users match the current filters.</div> : null}
        </div>
      </SectionCard>
    </ProtectedPage>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
