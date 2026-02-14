import React, { useEffect, useState } from "react";
import CreatableSelect from "react-select/creatable";
import { get, put } from "../gateway";

interface Setting {
    key: string;
    value: string;
    value_type: string;
    description: string;
    category: string;
    is_public: boolean;
}

const SettingRow: React.FC<{
    setting: Setting;
    onSave: (key: string, value: string) => Promise<void>;
}> = ({ setting, onSave }) => {
    const [value, setValue] = useState(setting.value);
    const [isSaving, setIsSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);
    const [justSaved, setJustSaved] = useState(false);

    useEffect(() => {
        setValue(setting.value);
        setHasChanges(false);
    }, [setting.value]);

    const handleChange = async (newValue: string) => {
        setValue(newValue);
        if (setting.value_type === "bool") {
            setIsSaving(true);
            try {
                await onSave(setting.key, newValue);
                setHasChanges(false);
                setJustSaved(true);
                setTimeout(() => setJustSaved(false), 2000);
            } finally {
                setIsSaving(false);
            }
        } else {
            setHasChanges(newValue !== setting.value);
        }
    };

    const handleSave = async () => {
        if (!hasChanges) return;
        setIsSaving(true);
        try {
            await onSave(setting.key, value);
            setHasChanges(false);
        } finally {
            setIsSaving(false);
        }
    };

    const renderInput = () => {
        if (setting.value_type === "bool") {
            return (
                <div className="uk-flex uk-flex-middle">
                    <input
                        type="checkbox"
                        className="uk-checkbox"
                        checked={value === "true"}
                        onChange={(e) =>
                            handleChange(e.target.checked ? "true" : "false")
                        }
                        disabled={isSaving}
                    />
                    <span className="settings-status-message uk-margin-small-left uk-text-muted">
                        {isSaving && <span>Saving...</span>}
                        {justSaved && !isSaving && <span>Saved</span>}
                    </span>
                </div>
            );
        }

        if (setting.value_type === "list") {
            const items = JSON.parse(value || "[]");
            const options = items.map((item: string) => ({
                label: item,
                value: item,
            }));

            return (
                <CreatableSelect
                    isMulti
                    value={options}
                    onChange={(newValues) => {
                        const newItems = newValues.map((v) => v.value);
                        setValue(JSON.stringify(newItems));
                        setHasChanges(true);
                    }}
                    placeholder="Type and press Enter to add..."
                    isDisabled={isSaving}
                />
            );
        }

        return (
            <input
                type="text"
                className="uk-input"
                value={value}
                onChange={(e) => handleChange(e.target.value)}
                disabled={isSaving}
            />
        );
    };

    return (
        <div className="settings-row">
            <div className="settings-row-left">
                <label className="uk-form-label uk-text-bold settings-label">
                    {setting.key.replace(/_/g, " ")}
                </label>
                <div className="uk-text-small uk-text-muted">
                    {setting.description}
                </div>
            </div>
            <div className="settings-row-right">
                <div className="settings-input-wrapper">{renderInput()}</div>
                {hasChanges && setting.value_type !== "bool" && (
                    <div className="settings-save-button-container">
                        <button
                            className="uk-button uk-button-primary uk-button-small"
                            onClick={handleSave}
                            disabled={isSaving}
                        >
                            {isSaving ? "Saving..." : "Save"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default function GlobalSettings() {
    const [settings, setSettings] = useState<Setting[]>([]);
    const [loading, setLoading] = useState(true);

    const loadSettings = async () => {
        try {
            const response = await get({ url: "/settings" });
            if (response && response.data) {
                setSettings(response.data);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSettings();
    }, []);

    const handleSave = async (key: string, value: string) => {
        await put({
            url: `/settings/${key}`,
            data: { value },
            expectedDataStatus: null,
        });
        await loadSettings();
    };

    if (loading) {
        return <div className="uk-text-center">Loading...</div>;
    }

    const groupedSettings: Record<string, Setting[]> = {};
    settings.forEach((setting) => {
        const category = setting.category;
        if (!groupedSettings[category]) {
            groupedSettings[category] = [];
        }
        groupedSettings[category].push(setting);
    });

    return (
        <div>
            <h2>Settings</h2>
            <p className="uk-text-muted">
                Configure global settings for the application
            </p>
            {Object.entries(groupedSettings).map(
                ([category, categorySettings]) => (
                    <div key={category} className="uk-margin-medium">
                        <h3 className="uk-heading-divider settings-category-heading">
                            {category}
                        </h3>
                        <div className="uk-card uk-card-default uk-card-body">
                            {categorySettings.map((setting) => (
                                <SettingRow
                                    key={setting.key}
                                    setting={setting}
                                    onSave={handleSave}
                                />
                            ))}
                        </div>
                    </div>
                ),
            )}
        </div>
    );
}
