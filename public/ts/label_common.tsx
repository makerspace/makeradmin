import { LabelMaxRelativeDays } from "frontend_common";
import { useState } from "preact/hooks";
import { Translator, useTranslation } from "./i18n";

export const DeleteButton = ({
    labelId,
    onDelete,
}: {
    labelId: number;
    onDelete: (labelId: number) => Promise<void>;
}) => {
    const { t } = useTranslation("labels");
    const [confirm, setConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const handleClick = async (e: any) => {
        e.preventDefault();
        if (!confirm) {
            setConfirm(true);
            return;
        }
        setLoading(true);
        try {
            await onDelete(labelId);
        } finally {
            setLoading(false);
        }
    };
    return (
        <button
            type="button"
            className={`uk-button confirm-button uk-icon ${
                confirm ? "confirm uk-button-danger" : ""
            }`}
            uk-icon="trash"
            title={t("delete_label")}
            disabled={loading}
            onClick={handleClick}
        >
            <span>Confirm</span>
        </button>
    );
};

export const dateToRelative = (
    now: Date,
    date: Date,
    t: Translator<"labels">,
    mode: "expiry" | "drying" | "generic",
) => {
    const diffMs = date.getTime() - now.getTime();
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);

    // Show relative if within ±LabelMaxRelativeDays days
    if (Math.abs(diffDay) < LabelMaxRelativeDays) {
        if (diffDay === 0) {
            if (Math.abs(diffHour) < 24) {
                if (diffHour === 0) {
                    if (Math.abs(diffMin) < 60) {
                        if (diffMin === 0) {
                            return t(`relative_${mode}.now`);
                        }
                        return t(
                            diffMin > 0
                                ? `relative_${mode}.in_minutes`
                                : `relative_${mode}.minutes_ago`,
                            { count: Math.abs(diffMin) },
                        );
                    }
                    return t(
                        diffHour > 0
                            ? `relative_${mode}.in_hours`
                            : `relative_${mode}.hours_ago`,
                        { count: Math.abs(diffHour) },
                    );
                }
                return t(
                    diffHour > 0
                        ? `relative_${mode}.in_hours`
                        : `relative_${mode}.hours_ago`,
                    { count: Math.abs(diffHour) },
                );
            }
            return t(
                diffDay > 0
                    ? `relative_${mode}.in_days`
                    : `relative_${mode}.days_ago`,
                { count: Math.abs(diffDay) },
            );
        }
        return t(
            diffDay > 0
                ? `relative_${mode}.in_days`
                : `relative_${mode}.days_ago`,
            { count: Math.abs(diffDay) },
        );
    }

    // Otherwise, show absolute
    const fourMonthsMs = 4 * 30 * 24 * 60 * 60 * 1000;
    let options: Intl.DateTimeFormatOptions = {
        month: "short",
        day: "numeric",
        hour: undefined,
        minute: undefined,
    };
    if (Math.abs(date.getTime() - now.getTime()) > fourMonthsMs) {
        // Several months difference, include year
        options.year = "numeric";
    }
    const date_str = date.toLocaleString(undefined, options);
    return date.getTime() < now.getTime()
        ? t(`relative_${mode}.date_past`, { date: date_str })
        : t(`relative_${mode}.date_future`, { date: date_str });
};
