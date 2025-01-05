import React, { useEffect, useMemo, useRef, useState } from "react";
import { renderToString } from "react-dom/server";
import { Prompt } from "react-router";
import { get, post } from "../gateway";
import { notifySuccess } from "../message";
import Collection from "../Models/Collection";
import { ADD_LABACCESS_DAYS } from "../Models/ProductAction";
import Span, { filterCategory } from "../Models/Span";
import { dateTimeToStr, parseUtcDate, utcToday } from "../utils";
import Icon from "./icons";
import TextInput from "./TextInput";

function last_span_enddate(spans, category) {
    const last_span = filterCategory(spans, category).splice(-1)[0];
    if (last_span) {
        return last_span.enddate;
    }
    return null;
}

function isAccessValid(date) {
    return date && parseUtcDate(date) >= utcToday();
}

function DateView(props) {
    const is_valid = isAccessValid(props.date);
    let status, text;

    if (!props.date) {
        status = (
            <div className="uk-panel-badge uk-badge uk-badge-warning">
                Saknas
            </div>
        );
        text = (
            <p style={{ color: "gray", fontStyle: "italic" }}>
                {props.placeholder}
            </p>
        );
    } else if (!is_valid) {
        status = (
            <div className="uk-panel-badge uk-badge uk-badge-danger">
                Utgånget
            </div>
        );
        text = (
            <p>
                Giltigt till:{" "}
                <span style={{ color: "red", fontStyle: "italic" }}>
                    {props.date}
                </span>
            </p>
        );
    } else {
        status = (
            <div className="uk-panel-badge uk-badge uk-badge-success">OK</div>
        );
        text = <p>Giltigt till: {props.date}</p>;
    }

    // Override if there are pending days to be synchronized
    if (props.pending || is_valid) {
        status = (
            <div className="uk-panel-badge uk-badge uk-badge-success">OK</div>
        );
    }

    return (
        <div className="uk-panel uk-panel-box">
            <p style={{ fontSize: "1.2em" }}>
                <b>{props.title}</b>
            </p>
            {status}
            {text}
            {props.pending ? (
                <p>
                    <span>
                        (<b>{props.pending}</b> dagar kommer läggas till vid en
                        nyckelsynkronisering)
                    </span>
                </p>
            ) : null}
        </div>
    );
}

function KeyHandoutForm(props) {
    const { member } = props;
    const [can_save_member, setCanSaveMember] = useState(false);
    const [pending_labaccess_days, setPendingLabaccessDays] = useState("?");
    const [labaccess_enddate, setLabaccessEnddate] = useState("");
    const [membership_enddate, setMembershipEnddate] = useState("");
    const [special_enddate, setSpecialEnddate] = useState("");
    const [accessy_in_org, setAccessyInOrg] = useState(false);
    const [accessy_groups, setAccessyGroups] = useState([]);
    const [accessy_pending_invites, setAccessyPendingInvites] = useState(0);

    const unsubscribe = useRef([]);
    const spanCollection = useMemo(
        () =>
            new Collection({
                type: Span,
                url: `/membership/member/${member.id}/spans`,
                pageSize: 0,
            }),
        [member.id],
    );

    const save = () => {
        let promise = Promise.resolve();
        if (member.isDirty() && member.canSave()) {
            promise = promise.then(() => member.save());
        }

        return promise;
    };

    const fetchAccessyStatus = () => {
        return get({ url: `/membership/member/${member.id}/access` }).then(
            (r) => {
                setAccessyPendingInvites(r.data.pending_invite_count);
                setAccessyInOrg(r.data.in_org);
                setAccessyGroups(r.data.access_permission_group_names);
            },
        );
    };

    const fetchPendingLabaccess = () => {
        return get({
            url: `/membership/member/${member.id}/pending_actions`,
        }).then((r) => {
            const sum_pending_labaccess_days = r.data.reduce((acc, value) => {
                if (value.action.action === ADD_LABACCESS_DAYS)
                    return acc + value.action.value;
                return acc;
            }, 0);
            setPendingLabaccessDays(sum_pending_labaccess_days);
        });
    };

    useEffect(() => {
        unsubscribe.current.push(
            member.subscribe(() => setCanSaveMember(member.canSave())),
        );
        unsubscribe.current.push(member.subscribe(() => fetchAccessyStatus()));
        unsubscribe.current.push(
            spanCollection.subscribe(({ items }) => {
                setLabaccessEnddate(last_span_enddate(items, "labaccess"));
                setMembershipEnddate(last_span_enddate(items, "membership"));
                setSpecialEnddate(
                    last_span_enddate(items, "special_labaccess"),
                );
            }),
        );

        fetchPendingLabaccess();
        fetchAccessyStatus();

        return () => {
            unsubscribe.current.forEach((u) => u());
        };
    }, [member.id]);

    const has_signed = member.labaccess_agreement_at !== null;

    const AccessyInviteSaveButton = () => {
        let tooltip;
        let color;

        if (
            !pending_labaccess_days &&
            !isAccessValid(labaccess_enddate) &&
            !isAccessValid(special_enddate)
        ) {
            tooltip =
                "Ingen labaccess, accessy invite kommer inte att skickas (bara sparning görs)!";
            color = "uk-button-danger";
        } else if (!has_signed) {
            tooltip =
                "Inte signerat, accessy invite kommer inte att skickas (bara sparning görs)!";
            color = "uk-button-danger";
        } else if (!member.phone) {
            tooltip =
                "Inget telefonnummer, accessy invite kommer inte att skickas (bara sparning görs)!";
            color = "uk-button-danger";
        } else {
            tooltip = "All info finns, accessy invite kommer att skickas!";
            color = "uk-button-primary";
        }

        const on_click = (e) => {
            e.preventDefault();
            save()
                .then(() =>
                    post({
                        url: `/webshop/member/${member.id}/ship_labaccess_orders`,
                        expectedDataStatus: "ok",
                    }),
                )
                .then(() => fetchPendingLabaccess())
                .then(() => spanCollection.fetch())
                .then(() => fetchAccessyStatus())
                .then(() => {
                    if (accessy_in_org) {
                        notifySuccess("Medlem redan i Makerspace Accessy org");
                    } else {
                        notifySuccess("Accessy invite skickad");
                    }
                });
            return false;
        };

        return (
            <button
                className={"uk-button uk-float-right " + color}
                title={tooltip}
                style={{ marginRight: "10px" }}
                tabIndex="1"
                onClick={on_click}
            >
                <Icon icon="save" /> Spara, lägg till labaccess och skicka
                Accessy-invite
            </button>
        );
    };

    let accessy_paragraph;
    if (accessy_in_org) {
        accessy_paragraph = (
            <p>
                <span className="uk-badge uk-badge-success">OK</span> Personen
                är med i organisationen. <br /> Med i följande (
                {accessy_groups.length}) grupper:{" "}
                {accessy_groups.sort().join(", ")}{" "}
            </p>
        );
    } else {
        let invite_part;
        if (accessy_pending_invites === 0) {
            invite_part = (
                <span className="uk-badge uk-badge-warning">Invite saknas</span>
            );
        } else {
            invite_part = (
                <span className="uk-badge uk-badge-success">
                    Invite skickad
                </span>
            );
        }
        accessy_paragraph = (
            <p>
                <span className="uk-badge uk-badge-danger">Ej access</span>{" "}
                Personen är inte med i organisationen ännu. <br /> {invite_part}{" "}
                Det finns {accessy_pending_invites} aktiva inbjudningar utsända
                för tillfället.{" "}
            </p>
        );
    }

    const section2andon = (
        <>
            <div className="uk-section">
                <h2>2. Kontrollera legitimation</h2>
                <p>
                    Kontrollera personens legitimation och för in personnummret
                    i fältet nedan. Nyckel kan endast lämnas ut till personen
                    som skall bli medlem.
                </p>
                <div>
                    <TextInput
                        model={member}
                        icon="birthdaycake"
                        tabIndex="1"
                        name="civicregno"
                        title="Personnummer"
                        placeholder="YYYYMMDD-XXXX"
                    />
                </div>
            </div>

            <div className="uk-section">
                <h2>3. Övrig information</h2>
                <p>
                    Kontrollera <b>epost</b> så personen kommer åt kontot, och{" "}
                    <b>telefon</b> så att de kan använda accessy.
                </p>
                <div className="uk-grid">
                    <div className="uk-width-1-1">
                        <TextInput
                            model={member}
                            icon="at"
                            name="email"
                            tabIndex="1"
                            type="email"
                            title="Epost"
                        />
                    </div>
                    <div className="uk-width-1-2">
                        <TextInput
                            model={member}
                            icon="phone"
                            name="phone"
                            tabIndex="1"
                            type="tel"
                            title="Telefonnummer"
                        />
                    </div>
                    <div className="uk-width-1-2">
                        <TextInput
                            model={member}
                            icon="home"
                            name="address_zipcode"
                            tabIndex="1"
                            type="number"
                            title="Postnummer"
                        />
                    </div>
                </div>
            </div>

            <div className="uk-section">
                <h2>4. Kontrollera medlemskap </h2>
                <p>
                    Kontrollera om medlemmen har köpt medlemskap och
                    labbmedlemskap.
                </p>
                <div>
                    <DateView
                        title="Föreningsmedlemskap"
                        date={membership_enddate}
                        placeholder="Inget tidigare medlemskap finns registrerat"
                    />
                    <DateView
                        title="Labaccess"
                        date={labaccess_enddate}
                        placeholder="Ingen tidigare labaccess finns registrerad"
                        pending={pending_labaccess_days}
                    />
                    {special_enddate ? (
                        <DateView
                            title="Specialaccess"
                            date={special_enddate}
                        />
                    ) : null}
                </div>
            </div>

            <div className="uk-section">
                <h2>5. Kontrollera tillgång till Accessy </h2>
                {accessy_paragraph}
            </div>

            <div style={{ paddingBottom: "4em" }}>
                <button
                    className="uk-button uk-button-primary uk-float-right"
                    tabIndex="2"
                    title="Spara ändringar"
                    disabled={!can_save_member}
                >
                    <Icon icon="save" /> Spara
                </button>
                <AccessyInviteSaveButton />
            </div>
        </>
    );

    return (
        <>
            <Prompt
                when={can_save_member}
                message="Du har inte sparat - vill du verkligen lämna sidan?"
            ></Prompt>
            <div className="meep">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        save();
                        return false;
                    }}
                >
                    <div className="uk-section">
                        <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                        <p>
                            Kontrollera att labbmedlemsavtalet är signerat och
                            säkerställ att rätt medlemsnummer står väl synligt
                            på labbmedlemsavtalet.
                        </p>
                        <div>
                            <label htmlFor="signed">
                                <input
                                    id="signed"
                                    style={{ verticalAlign: "middle" }}
                                    className="uk-checkbox"
                                    type="checkbox"
                                    tabIndex="1"
                                    checked={has_signed}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            member.labaccess_agreement_at =
                                                new Date().toISOString();
                                        } else {
                                            UIkit.modal.confirm(
                                                renderToString(
                                                    <div>
                                                        <p>
                                                            Är du säker på{" "}
                                                            {member.firstname}{" "}
                                                            {member.lastname}{" "}
                                                            inte har skrivit på
                                                            ett labbavtal?
                                                        </p>
                                                        <p>
                                                            Labbavtalet mottogs{" "}
                                                            <strong>
                                                                {dateTimeToStr(
                                                                    member.labaccess_agreement_at,
                                                                )}
                                                            </strong>
                                                            .{" "}
                                                        </p>
                                                    </div>,
                                                ),
                                                function () {
                                                    member.labaccess_agreement_at =
                                                        null;
                                                },
                                                false,
                                            );
                                        }
                                    }}
                                />{" "}
                                &nbsp; Signerat labbmedlemsavtal mottaget
                                {has_signed
                                    ? " " +
                                      dateTimeToStr(
                                          member.labaccess_agreement_at,
                                      )
                                    : ""}
                                .
                            </label>
                        </div>
                    </div>
                    {has_signed ? section2andon : ""}
                </form>
            </div>
        </>
    );
}

export default KeyHandoutForm;
