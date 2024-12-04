import React, { useEffect, useState } from "react";
import CategoryPeriodsInput from "../Components/CategoryPeriodsInput";
import CategoryPeriods from "../Models/CategoryPeriods";
import { calculateSpanDiff, filterPeriods } from "../Models/Span";
import auth from "../auth";
import { post } from "../gateway";

export default function MembershipPeriodsInput(props) {
    const [showHistoric, setShowHistoric] = useState(true);
    const [saveDisabled, setSaveDisabled] = useState(true);

    const categoryPeriodsList = [
        new CategoryPeriods({ category: "labaccess" }),
        new CategoryPeriods({ category: "membership" }),
        new CategoryPeriods({ category: "special_labaccess" }),
    ];

    const canSave = () => {
        return (
            categoryPeriodsList.every((c) => c.isValid()) &&
            categoryPeriodsList.some((c) => c.isDirty())
        );
    };

    useEffect(() => {
        const unsubscribe = [];
        unsubscribe.push(
            props.spans.subscribe(({ items }) => {
                categoryPeriodsList.forEach((periods) =>
                    periods.replace(filterPeriods(items, periods.category)),
                );
            }),
        );
        categoryPeriodsList.forEach((cp) => {
            unsubscribe.push(cp.subscribe(() => setSaveDisabled(!canSave())));
        });

        return () => {
            unsubscribe.forEach((u) => u());
        };
    }, [props.spans, categoryPeriodsList]);

    const onSave = () => {
        const deleteSpans = [];
        const addSpans = [];
        categoryPeriodsList.forEach((cp) => {
            cp.merge();
            calculateSpanDiff({
                items: props.spans.items,
                categoryPeriods: cp,
                member_id: props.member_id,
                deleteSpans,
                addSpans,
            });
        });

        const deleteIds = deleteSpans.map((s) => s.id).join(",");
        const timestamp = new Date().getTime().toString();
        addSpans.forEach(
            (s, i) =>
                (s.creation_reason = (
                    timestamp +
                    i +
                    " gui_edit:" +
                    auth.getUsername() +
                    " replacing:" +
                    deleteIds
                ).slice(0, 255)),
        );

        const promises = [];
        promises.push(...deleteSpans.map((s) => s.del()));
        promises.push(...addSpans.map((s) => s.save()));
        Promise.all(promises).then(() => {
            props.spans.fetch();

            post({
                url: `/webshop/member/${props.member_id}/ship_labaccess_orders`,
                expectedDataStatus: "ok",
            });
        });
    };

    return (
        <form
            className="uk-form"
            onSubmit={(e) => {
                e.preventDefault();
                onSave();
                return false;
            }}
        >
            <label className="uk-label" htmlFor="showHistoric">
                Visa historiska
            </label>
            <input
                id="showHistoric"
                className="uk-checkbox"
                type="checkbox"
                checked={showHistoric}
                onChange={(e) => setShowHistoric(e.target.checked)}
            />
            {categoryPeriodsList.map((cp) => (
                <CategoryPeriodsInput
                    key={cp.category}
                    categoryPeriods={cp}
                    showHistoric={showHistoric}
                />
            ))}
            <button
                disabled={saveDisabled}
                className="uk-button uk-button-success uk-float-right"
            >
                <i className="uk-icon-save" /> Spara
            </button>
        </form>
    );
}
