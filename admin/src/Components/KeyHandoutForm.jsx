import React from "react";
import { Prompt } from "react-router";
import TextInput from "./TextInput";
import { withRouter } from "react-router";
import Span, { filterCategory } from "../Models/Span";
import Collection from "../Models/Collection";
import { ADD_LABACCESS_DAYS } from "../Models/ProductAction";
import { dateTimeToStr, parseUtcDate, utcToday } from "../utils";
import { get, post } from "../gateway";
import { notifySuccess } from "../message";
import { renderToString } from "react-dom/server";

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

class KeyHandoutForm extends React.Component {
    constructor(props) {
        super(props);
        const { member } = this.props;
        this.state = {
            can_save_member: false,
            pending_labaccess_days: "?",
            labaccess_enddate: "",
            membership_enddate: "",
            special_enddate: "",
            accessy_in_org: false,
            accessy_groups: [],
            accessy_pending_invites: 0,
        };
        this.unsubscribe = [];
        this.spanCollection = new Collection({
            type: Span,
            url: `/membership/member/${member.id}/spans`,
            pageSize: 0,
        });
        this.save = this.save.bind(this);
        this.fetchPendingLabaccess();
        this.fetchAccessyStatus();
    }

    save() {
        let promise = Promise.resolve();
        const { member } = this.props;
        if (member.isDirty() && member.canSave()) {
            promise.then(() => member.save());
        }

        return promise;
    }

    fetchAccessyStatus() {
        const { member } = this.props;
        return get({ url: `/membership/member/${member.id}/access` }).then(
            (r) => {
                this.setState({
                    accessy_pending_invites: r.data.pending_invite_count,
                    accessy_in_org: r.data.in_org,
                    accessy_groups: r.data.access_permission_group_names,
                });
            },
        );
    }

    fetchPendingLabaccess() {
        const { member } = this.props;
        return get({
            url: `/membership/member/${member.id}/pending_actions`,
        }).then((r) => {
            const sum_pending_labaccess_days = r.data.reduce((acc, value) => {
                if (value.action.action === ADD_LABACCESS_DAYS)
                    return acc + value.action.value;
                return acc;
            }, 0);
            this.setState({
                pending_labaccess_days: sum_pending_labaccess_days,
            });
        });
    }

    componentDidMount() {
        const { member } = this.props;
        this.unsubscribe.push(
            member.subscribe(() =>
                this.setState({ can_save_member: member.canSave() }),
            ),
        );
        this.unsubscribe.push(
            member.subscribe(() => this.fetchAccessyStatus()),
        );
        this.unsubscribe.push(
            this.spanCollection.subscribe(({ items }) => {
                this.setState({
                    labaccess_enddate: last_span_enddate(items, "labaccess"),
                    membership_enddate: last_span_enddate(items, "membership"),
                    special_enddate: last_span_enddate(
                        items,
                        "special_labaccess",
                    ),
                });
            }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe.forEach((u) => u());
    }

    renderAccessyInviteSaveButton({
        has_signed,
        labaccess_enddate,
        special_enddate,
        pending_labaccess_days,
        member,
    }) {
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
            color = "uk-button-success";
        }

        const on_click = (e) => {
            e.preventDefault();
            this.save()
                .then(() =>
                    post({
                        url: `/webshop/member/${member.id}/ship_labaccess_orders`,
                        expectedDataStatus: "ok",
                    }),
                )
                .then(() => this.fetchPendingLabaccess())
                .then(() => this.spanCollection.fetch())
                .then(() => this.fetchAccessyStatus())
                .then(() => {
                    if (this.state.accessy_in_org) {
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
                <i className="uk-icon-save" /> Spara, lägg till labaccess och
                skicka Accessy-invite
            </button>
        );
    }

    render() {
        const { member } = this.props;
        const {
            can_save_member,
            labaccess_enddate,
            membership_enddate,
            special_enddate,
            pending_labaccess_days,
        } = this.state;
        const { accessy_groups, accessy_in_org, accessy_pending_invites } =
            this.state;
        const has_signed = member.labaccess_agreement_at !== null;

        let accessy_paragraph;
        if (accessy_in_org) {
            accessy_paragraph = (
                <p>
                    <span className="uk-badge uk-badge-success">OK</span>{" "}
                    Personen är med i organisationen. <br /> Med i följande (
                    {accessy_groups.length}) grupper:{" "}
                    {accessy_groups.sort().join(", ")}{" "}
                </p>
            );
        } else {
            let invite_part;
            if (accessy_pending_invites === 0) {
                invite_part = (
                    <span className="uk-badge uk-badge-warning">
                        Invite saknas
                    </span>
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
                    Personen är inte med i organisationen ännu. <br />{" "}
                    {invite_part} Det finns {accessy_pending_invites} aktiva
                    inbjudningar utsända för tillfället.{" "}
                </p>
            );
        }

        // Section 2 and onward shall only be visible after lab contract has been signed
        const section2andon = (
            <>
                <div className="uk-section">
                    <h2>2. Kontrollera legitimation</h2>
                    <p>
                        Kontrollera personens legitimation och för in
                        personnummret i fältet nedan. Nyckel kan endast lämnas
                        ut till personen som skall bli medlem.
                    </p>
                    <div>
                        <TextInput
                            model={member}
                            icon="birthday-cake"
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
                        Kontrollera <b>epost</b> så personen kommer åt kontot,
                        och <b>telefon</b> så att de kan använda accessy.
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
                        className="uk-button uk-button-success uk-float-right"
                        tabIndex="2"
                        title="Spara ändringar"
                        disabled={!can_save_member}
                    >
                        <i className="uk-icon-save" /> Spara
                    </button>
                    {this.renderAccessyInviteSaveButton({
                        has_signed,
                        labaccess_enddate,
                        special_enddate,
                        pending_labaccess_days,
                        member,
                    })}
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
                        className="uk-form"
                        onSubmit={(e) => {
                            e.preventDefault();
                            this.save();
                            return false;
                        }}
                    >
                        <div className="uk-section">
                            <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                            <p>
                                Kontrollera att labbmedlemsavtalet är signerat
                                och säkerställ att rätt medlemsnummer står väl
                                synligt på labbmedlemsavtalet.
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
                                                                Är du säker på
                                                                att{" "}
                                                                {
                                                                    member.firstname
                                                                }{" "}
                                                                {
                                                                    member.lastname
                                                                }{" "}
                                                                inte har skrivit
                                                                på ett
                                                                labbavtal?
                                                            </p>
                                                            <p>
                                                                Labbavtalet
                                                                mottogs{" "}
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
}

export default withRouter(KeyHandoutForm);
