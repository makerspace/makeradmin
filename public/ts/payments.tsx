import * as common from "./common"
import * as login from "./login"
import { ServerResponse, UNAUTHORIZED } from "./common";
import { Component, render } from 'preact';
import { kontonummer as validate_account_number } from './kontonummer';

declare var UIkit: any;

enum PaymentState {
    PaidSelf = "paid_self",
    MakerspaceToPayInvoice = "makerspace_to_pay_invoice",
    PaidByMakerspace = "paid_by_makerspace",
}

function paymentStateDescription(state: PaymentState): string {
    switch (state) {
        case PaymentState.PaidSelf:
            return "Paid by me";
        case PaymentState.MakerspaceToPayInvoice:
            return "Makerspace should pay attached invoice";
        case PaymentState.PaidByMakerspace:
            return "Paid using a makerspace account";
    }
}

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const rootElement = document.querySelector("#economy-payment") as HTMLElement;
    rootElement.innerHTML = "";

    const usages = [
        {
            id: "sold_at_makerspace",
            label: "For sale at the makerspace",
        },
        {
            id: "consumables",
            label: "Consumables",
        },
        {
            id: "new",
            label: "New item & tools",
        },
        {
            id: "upgrades",
            label: "Upgrades",
        },
        {
            id: "maintenance",
            label: "Maintenance",
        },
        {
            id: "other",
            label: "Other",
        },
    ]

    const areas = [
        {
            id: "location:wood_workshop",
            label: "Wood workshop",
        },
        {
            id: "location:metal_workshop",
            label: "Metal workshop",
        },
        {
            id: "location:welding_room",
            label: "Welding room",
        },
        {
            id: "location:laser_cutter",
            label: "Laser cutter",
        },
        {
            id: "location:wood_cnc",
            label: "Wood CNC",
        },
        {
            id: "location:3d_printing",
            label: "3D Printing",
        },
        {
            id: "location:electronics_corner",
            label: "Electronics corner",
        },
        {
            id: "location:sewing_room",
            label: "Sewing room",
        },
        {
            id: "location:vinyl_corner",
            label: "Vinyl corner",
        },
        {
            id: "location:painting_room",
            label: "Painting room",
        },
        {
            id: "location:workshop_room",
            label: "Workshop room",
        },
        {
            id: "location:other",
            label: "Other location",
        },
        {
            id: "location:whole_space",
            label: "The whole space",
        },
        {
            id: "it",
            label: "IT",
        },
        {
            id: "software",
            label: "Software",
        },
        {
            id: "makerspace_board",
            label: "The board",
        },
        {
            id: "food",
            label: "Food",
        },
    ];

    const valid_payment_states = [
        PaymentState.PaidSelf,
        PaymentState.MakerspaceToPayInvoice,
        PaymentState.PaidByMakerspace,
    ];

    const member_id = "2644";

    const approving_members = [
        {
            id: "3000",
            label: "Erik Cederberg",
        },
        {
            id: "3001",
            label: "Mysterious Person",
        },
        {
            id: "2644",
            label: "Aron Granberg",
        },
    ];

    // Sort the current user at the top (if the current user can approve it)
    approving_members.sort((a, b) => {
        return (b.id === member_id ? 1 : 0) - (a.id === member_id ? 1 : 0)
    })

    // Create your app
    const app = <EconomyItem usages={usages} areas={areas} valid_payment_states={valid_payment_states} valid_approving_members={approving_members} member_id={member_id} />;
    // h('h1', null, 'Hello World!');

    render(app, rootElement);
});

interface ActiveUsage {
    id: string,
    fraction: number
}

interface EconomyItemSubmission {
    name: string
    active_usages: ActiveUsage[],
    active_areas: ActiveUsage[],
    amount: number
    attached_files: string[],
    payment_state: PaymentState
    target_bank_account: string
    approved_by: string
}

enum UploadState {
    Idle,
    Uploading,
}

class EconomyItemState {
    name: string = ""
    active_usages: Map<string, number> = new Map<string, number>()
    active_areas: Map<string, number> = new Map<string, number>()
    amount: number | null = null
    attached_files: AttachedFile[] = []
    payment_state: PaymentState | null = null
    target_bank_account: string = ""
    approved_by: string|null = null

    upload_state: UploadState = UploadState.Idle
    error_message: string | null = null
}

interface AttachedFile {
    file: File,
    temporary_url: string,
    uploaded_id: string | null,
}

interface LabelWithID {
    id: string,
    label: string,
}

type UsageItem = LabelWithID;
type AreaItem = LabelWithID;

interface ApprovingMember {
    id: string,
    label: string,
}

interface EconomyItemProps {
    usages: UsageItem[],
    areas: AreaItem[],
    valid_payment_states: PaymentState[],
    valid_approving_members: ApprovingMember[],
    member_id: string,
}

function totalValue(map: Map<string, number>) {
    let sum = 0;
    for (const value of map.values()) {
        sum += value;
    }
    return sum;
}

function normalizeMap(map: Map<string, number>) {
    const sum = totalValue(map);
    if (sum > 0) {
        for (const key of map.keys()) {
            let v = map.get(key)! / sum;
            map.set(key, v);
        }
    }
}

function meanValue(map: Map<string, number>): number {
    let sum = 0;
    for (const value of map.values()) {
        sum += value;
    }
    if (sum > 0) {
        return sum / map.size;
    } else {
        return 1.0;
    }
}

function mimeToIconName(mime: string): string {
    if (mime == "application/pdf") {
        return "file-pdf";
    } else {
        return "file"
    }
}

function removeFirstItem<T>(arr: T[], value: T) {
    var index = arr.indexOf(value);
    if (index > -1) {
        arr.splice(index, 1);
    }
    return arr;
}

function simplifyBankAccount(account: string): string {
    console.log(account);
    account = account.replace("-", " ").replace("_", " ").replace(",", "").replace(".", "").replace("\t", " ");
    // Collapse multiple spaces
    account = account.replace(/\s\s+/, " ");
    console.log(account);

    const validation = validate_account_number(account);
    if (validation !== false) {
        account = validation.clearing_number + " " + validation.account_number;
    }

    return account;
}

class EconomyItem extends Component<EconomyItemProps, EconomyItemState> {
    constructor(props: EconomyItemProps) {
        super(props)
        let initial_state = new EconomyItemState();
        if (this.props.valid_approving_members.find(x => x.id == this.props.member_id) !== undefined) {
            initial_state.approved_by = this.props.member_id;
        }

        this.state = initial_state;
    }

    setUsageActive(usageID: string, active: boolean) {
        if (active) {
            this.state.active_usages.set(usageID, meanValue(this.state.active_usages));
        } else {
            this.state.active_usages.delete(usageID);
        }
        normalizeMap(this.state.active_usages);
        this.setState({ active_usages: this.state.active_usages })
    }

    setAreaActive(areaID: string, active: boolean) {
        if (active) {
            this.state.active_areas.set(areaID, meanValue(this.state.active_areas));
        } else {
            this.state.active_areas.delete(areaID);
        }
        normalizeMap(this.state.active_areas);
        this.setState({ active_areas: this.state.active_areas })
    }

    async submit_internal(): Promise<EconomyItemSubmission | string> {
        let active_areas = new Map(this.state.active_areas);
        normalizeMap(active_areas);
        let active_usages = new Map(this.state.active_usages);
        normalizeMap(active_usages);

        const amount = this.state.amount;
        if (amount === null) return "Please specify the total amount";

        const payment_state = this.state.payment_state;
        if (payment_state === null) return "Please specify how the item was paid";

        const approved_by = this.state.approved_by;
        if (approved_by === null) return "Please specify who approved this purchase";

        const target_bank_account = this.state.target_bank_account;
        
        const attached_files = Array.from(this.state.attached_files);
        const uploads = attached_files.map(async file => {
            if (file.uploaded_id === null) {
                const response = await common.uploadFile<ServerResponse<string>>("", file.file);
                if (response.status != "ok") {
                    throw "Invalid response from server";
                }
                file.uploaded_id = response.data;
            }
            return file.uploaded_id;
        });
        const file_ids = await Promise.all(uploads);

        return {
            name: this.state.name,
            active_usages: Array.from(active_usages.entries()).map(([id, fraction]) => {
                return { id, fraction }
            }),
            active_areas: Array.from(active_areas.entries()).map(([id, fraction]) => {
                return { id, fraction }
            }),
            amount,
            attached_files: file_ids,
            payment_state,
            target_bank_account,
            approved_by: approved_by,
        }
    }

    submit() {
        console.log("Submitting");
        this.setState({upload_state: UploadState.Uploading});
        this.submit_internal().then(result => {
            if(typeof result === "string") {
                this.setState({error_message: result, upload_state: UploadState.Idle});
            } else {
                this.setState({error_message: null, upload_state: UploadState.Idle});
            }
        }).catch(e => {
            this.setState({error_message: e, upload_state: UploadState.Idle});
        });
        common.ajax("POST", "", this.state)
    }

    render(props: EconomyItemProps) {
        console.log(this.state);

        let sliderSection = null;
        if (this.state.active_areas.size == 2) {
            let [[idA, valueA], [idB, valueB]] = Array.from(this.state.active_areas.entries());
            const sum = valueA + valueB;
            if (sum > 0) {
                valueA = valueA / sum;
                valueB = valueB / sum;
            }
            const labelA = props.areas.find(x => x.id == idA)?.label;
            const labelB = props.areas.find(x => x.id == idB)?.label;
            console.log(valueA);

            sliderSection = (
                <div class="economy-item-slider">
                    <div class="economy-item-slider-labels">
                        <span>{labelA} {(valueA * 100).toFixed(0) + "%"}</span>
                        <span>{labelB} {(valueB * 100).toFixed(0) + "%"}</span>
                    </div>
                    <input type="range" min="0" max="100" value={valueA * 100} class="slider"
                        onInput={e => {
                            let valueA = parseFloat(e.currentTarget.value) / 100;
                            valueA = Math.max(valueA, 0.1);
                            valueA = Math.min(valueA, 0.9);
                            valueA = Math.round(valueA * 10) / 10;

                            let valueB = 1.0 - valueA;
                            console.log(valueA, valueB);

                            this.state.active_areas.set(idA, valueA);
                            this.state.active_areas.set(idB, valueB);
                            this.setState({ active_areas: this.state.active_areas });
                        }
                        } />
                </div>
            );
        } else if (this.state.active_areas.size > 2) {
            let sum = 0;
            for (const x of this.state.active_areas.values()) {
                sum += x;
            }

            let percentage_classes = "economy-percentage";
            if (sum < 1.0 - 0.0001) percentage_classes += " economy-percentage-low";
            if (sum > 1.0 + 0.0001) percentage_classes += " economy-percentage-high";

            sliderSection = <div>
                {Array.from(this.state.active_areas.entries()).map(([id, value]) => {
                    const label = props.areas.find(x => x.id == id)?.label;

                    return (
                        <div class="economy-item-slider">
                            <span>{label}</span>
                            <input type="number" min="0" max="100" value={Math.round(value * 100)} class="slider"
                                onInput={e => {
                                    let value = Math.round(parseFloat(e.currentTarget.value)) / 100;
                                    if (isFinite(value)) {
                                        this.state.active_areas.set(id, value);
                                        this.setState({ active_areas: this.state.active_areas });
                                    }
                                }
                                } />
                        </div>
                    )
                })}
                <p>Remaining percentage: <span class={percentage_classes}>{((1.0 - sum) * 100).toFixed(0) + "%"}</span></p>
            </div>
        }

        console.log(this.props.valid_approving_members);

        return (
            <form onSubmit={e=>{
                    this.submit();
                    e.preventDefault();
                    return false;
                }}>
                <div id="economy-payment" class="economy-payment">
                    <input type="text" class="economy-item-name" placeholder="Name" value={this.state.name} onInput={e => { console.log(this.state.name); this.setState({ name: e.currentTarget.value }) }} />
                    <h3>How will the item be used?</h3>
                    <div class="economy-item-usage">
                        {props.usages.map(item => {
                            const id = "usage_" + item.id;
                            return (
                                <label for={id}>
                                    <input
                                        id={id}
                                        type="checkbox"
                                        checked={this.state.active_usages.has(item.id)}
                                        onChange={e => {
                                            this.setUsageActive(item.id, e.currentTarget.checked)
                                        }}
                                    />
                                    <div>{item.label}</div>
                                </label>
                            )
                        })}
                    </div>

                    <h3>What area is the item for?</h3>
                    <div class="economy-payment-rooms">
                        {props.areas.map(item => {
                            const id = "usage_" + item.id;
                            return (
                                <label for={id}>
                                    <input
                                        id={id}
                                        type="checkbox"
                                        checked={this.state.active_areas.has(item.id)}
                                        onChange={e => {
                                            this.setAreaActive(item.id, e.currentTarget.checked)
                                        }}
                                    />
                                    <div>{item.label}</div>
                                </label>
                            )
                        })}
                    </div>

                    <div class="economy-item-percentages">
                        {sliderSection}
                    </div>

                    <div class="economy-item-wide-input-wrapper">
                        <input
                            autocomplete="off"
                            inputMode="numeric"
                            pattern="[\d\.,]+"
                            type="text"
                            class="economy-item-wide-input"
                            placeholder="Total sum (SEK)"
                            value={this.state.amount || ""}
                            onChange={e => {
                                // parseFloat will just stop parsing if it finds a space or a comma
                                const simplifiedValue = e.currentTarget.value.replace(" ", "").replace(",", ".");
                                let amount: number | null = parseFloat(simplifiedValue);
                                if (!isFinite(amount)) {
                                    amount = null;
                                }
                                this.setState({ amount })
                            }
                            }
                        />
                        <div>
                            SEK
                        </div>
                    </div>

                    <div class="receipt-drag-drop">
                        {
                            this.state.attached_files.map(file => {
                                return (<div class="file">
                                    <a target="_blank" class="filename" href={file.temporary_url} >{file.file.name}</a>
                                    {
                                        file.file.type.startsWith("image") ? (
                                            <a class="fileimage" target="_blank" href={file.temporary_url}><img src={file.temporary_url} /></a>
                                        ) : null
                                    }
                                    <div class="delete-btn" onClick={_e => {
                                        removeFirstItem(this.state.attached_files, file);
                                        this.setState({ attached_files: this.state.attached_files })
                                    }}>
                                        <i uk-icon="trash" />
                                    </div>
                                </div>);
                            })
                        }
                        <label for="receipt_file_input">Click to select receipts and invoices</label>
                        <input
                            id="receipt_file_input"
                            type="file"
                            multiple
                            accept="image/*,.pdf,.txt,.csv,.tsv,.zip"
                            onChange={e => {
                                const files = e.currentTarget.files!;
                                for (let i = 0; i < files.length; i++) {
                                    const file = files[i];
                                    console.log(file);
                                    const isImage = file.type.startsWith("image");
                                    this.state.attached_files.push({
                                        file,
                                        temporary_url: URL.createObjectURL(file),
                                        uploaded_id: null,
                                    });
                                    this.setState({ attached_files: this.state.attached_files });
                                }
                                e.currentTarget.files = null;
                            }
                            }
                        />

                        {/* <input type="file" multiple accept="image/*" capture="environment"> */}
                    </div>

                    <h3>How has it been paid?</h3>
                    <div class="economy-item-payment-state">
                        {
                            this.props.valid_payment_states.map(state => {
                                const id = "payment_state_" + state;
                                return (
                                    <>
                                        <input
                                            id={id}
                                            type="radio"
                                            name="payment_state"
                                            value={state}
                                            checked={this.state.payment_state === state}
                                            onClick={_ => this.setState({ payment_state: state })}
                                        />
                                        <label for={id}>{paymentStateDescription(state)}</label>
                                    </>
                                );
                            })
                        }
                    </div>

                    { this.state.payment_state == PaymentState.PaidSelf ? (
                        <>
                            <input
                                autocomplete="off"
                                inputMode="numeric"
                                pattern="[\d\- ]+"
                                type="text"
                                class="economy-item-wide-input economy-item-wide-input-wrapper"
                                placeholder="Your bank account number"
                                value={this.state.target_bank_account}
                                onChange={e =>
                                    this.setState({ target_bank_account: simplifyBankAccount(e.currentTarget.value) })
                                }
                            />

                            <AccountValidation account={this.state.target_bank_account} />
                        </>
                    )
                        : null
                    }

                    <h3>Who approved this purchase?</h3>

                    <select class="economy-item-dropdown" onChange={e=>{
                        let value = e.currentTarget.value;
                        // Note: will be null if the chosen id is invalid.
                        // For example if the default option is chosen.
                        let id = this.props.valid_approving_members.find(v => v.id == value)?.id || null;
                        this.setState({approved_by: id});
                    }}>
                        <option value="">Select...</option>
                        {
                            this.props.valid_approving_members.map(member => 
                                <option value={member.id}>Approved by {member.label}</option>
                            )
                        }
                    </select>

                    <button type="submit" class={this.state.upload_state == UploadState.Uploading ? "uploading" : ""}><span data-uk-spinner="" />Submit</button>
                </div>
            </form>
        )
    }
}

function AccountValidation({ account }: { account: string}) {
    if (account.trim().length == 0) return null;

    const output = validate_account_number(account);

    if (output !== false) {
        return null
        // return <div class="economy-info">
        //     Account number is valid!
        //     {output.bank_name}: {output.clearing_number} - {output.account_number}
        // </div>
    } else {
        return <div class="economy-info error">
            Account number is not valid. Please write it on the format "clearing number (space) account number".
        </div>
    }
}