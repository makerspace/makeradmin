import React, { useEffect, useState } from "react";
import CountryDropdown from "./CountryDropdown";
import DateTimeShow from "./DateTimeShow";
import TextInput from "./TextInput";

const MemberForm = ({ member, onSave, onDelete }) => {
    const [saveDisabled, setSaveDisabled] = useState(true);

    useEffect(() => {
        const unsubscribe = member.subscribe(() => {
            setSaveDisabled(!member.canSave());
        });

        return () => {
            unsubscribe();
        };
    }, [member]);

    return (
        <div className="meep">
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    onSave();
                    return false;
                }}
            >
                <fieldset>
                    <legend>
                        <i className="uk-icon-user" /> Personuppgifter
                    </legend>

                    <TextInput
                        margin={false}
                        model={member}
                        name="civicregno"
                        title="Personnummer"
                    />
                    <TextInput
                        model={member}
                        name="firstname"
                        title="Förnamn"
                    />
                    <TextInput
                        model={member}
                        name="lastname"
                        title="Efternamn"
                    />
                    <TextInput model={member} name="email" title="E-post" />
                    <TextInput
                        model={member}
                        name="phone"
                        title="Telefonnummer"
                    />
                </fieldset>

                <fieldset>
                    <legend>
                        <i className="uk-icon-home" /> Adress
                    </legend>

                    <TextInput
                        margin={false}
                        model={member}
                        name="address_street"
                        title="Adress"
                    />
                    <TextInput
                        model={member}
                        name="address_extra"
                        title="Adress extra"
                        placeholder="Extra adressrad, t ex C/O adress"
                    />
                    <div style={{ display: "flex" }}>
                        <div style={{ flex: "0 0 200px" }}>
                            <TextInput
                                model={member}
                                type="number"
                                name="address_zipcode"
                                title="Postnummer"
                            />
                        </div>
                        <div
                            style={{ flex: "1 1 auto" }}
                            className="uk-margin-left"
                        >
                            <TextInput
                                model={member}
                                name="address_city"
                                title="Postort"
                            />
                        </div>
                    </div>

                    <div>
                        <label
                            htmlFor="address_country"
                            className="uk-form-label"
                        >
                            Land
                        </label>
                        <CountryDropdown
                            model={member}
                            name="address_country"
                        />
                    </div>
                </fieldset>

                {!member.id ? (
                    ""
                ) : (
                    <fieldset>
                        <legend>
                            <i className="uk-icon-tag" /> Metadata
                        </legend>

                        <div className="form-row">
                            <label className="uk-form-label">
                                Medlem sedan
                            </label>
                            <div className="uk-form-controls">
                                <i className="uk-icon-calendar" />
                                &nbsp;
                                <DateTimeShow date={member.created_at} />
                            </div>
                        </div>

                        <div className="form-row">
                            <label className="uk-form-label">
                                Senast uppdaterad
                            </label>
                            <div className="uk-form-controls">
                                <i className="uk-icon-calendar" />
                                &nbsp;
                                <DateTimeShow date={member.updated_at} />
                            </div>
                        </div>
                    </fieldset>
                )}

                <div className="form-row">
                    {!member.id ? (
                        ""
                    ) : (
                        <a
                            className="uk-button uk-button-danger uk-float-left"
                            onClick={onDelete}
                        >
                            <i className="uk-icon-trash" /> Ta bort medlem
                        </a>
                    )}
                    <button
                        className="uk-button uk-button-primary uk-float-right"
                        disabled={saveDisabled}
                    >
                        <i className="uk-icon-save" />{" "}
                        {member.id ? "Spara" : "Skapa"}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default MemberForm;
