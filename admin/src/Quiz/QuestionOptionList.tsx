import React from "react";
import _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import QuizQuestionOption from "../Models/QuizQuestionOption";
import { confirmModal } from "../message";

// Save functions for each item. Debounced to avoid a ton of unnecessary saves
const debouncedSaves = new Map<QuizQuestionOption, () => void>();

const Row =
    (collection: Collection<QuizQuestionOption>, onChanged: () => void) =>
    ({ item }: { item: QuizQuestionOption }) => {
        const deleteItem = () => {
            return confirmModal(item.deleteConfirmMessage())
                .then(() => item.del())
                .then(
                    () => collection.fetch(),
                    () => null,
                );
        };

        if (!debouncedSaves.has(item))
            debouncedSaves.set(
                item,
                _.debounce(() => item.save(), 300),
            );

        return (
            <tr key={item.id}>
                <td>
                    <input
                        className="uk-input uk-width-1-1"
                        type="text"
                        value={item.description}
                        onChange={(v) => {
                            ((item.description = v.target.value), onChanged());
                            debouncedSaves.get(item)!();
                        }}
                    />
                </td>
                <td>
                    <input
                        className="uk-checkbox"
                        type="checkbox"
                        checked={item.correct}
                        onChange={(v) => {
                            ((item.correct = v.target.checked), onChanged());
                            debouncedSaves.get(item)!();
                        }}
                    />
                </td>
                <td>
                    <a onClick={deleteItem} className="removebutton">
                        <Icon icon="trash" />
                    </a>
                </td>
            </tr>
        );
    };

interface State {
    saveEnabled: boolean;
}

interface Props {
    question_id: number;
}

class QuestionOptionList extends React.Component<Props, State> {
    collection: Collection<QuizQuestionOption>;
    option: QuizQuestionOption;

    constructor(props: Props) {
        super(props);
        const id = props.question_id;
        this.collection = new Collection<QuizQuestionOption>({
            type: QuizQuestionOption,
            url: `/quiz/question/${id}/options`,
            idListName: "options",
            pageSize: 0,
        });
        this.option = new QuizQuestionOption({ question_id: id });
        this.state = { saveEnabled: false };
    }

    override componentDidMount() {}

    override componentWillUnmount() {}

    createOption() {
        this.option.description = "Nytt svarsalternativ!";
        this.option.save().then(() => {
            this.option.reset({ question_id: this.props.question_id });
            this.collection.fetch();
        });
    }

    override render() {
        const columns = [{ title: "Svarsalternativ" }, { title: "Korrekt" }];

        const id = this.props.question_id;
        const { saveEnabled } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <CollectionTable
                        emptyMessage="Inga svarsalternativ finns"
                        rowComponent={Row(this.collection, () =>
                            this.setState({}),
                        )}
                        collection={this.collection}
                        columns={columns}
                        className="uk-table-middle"
                    />
                </div>
                <button
                    onClick={() => this.createOption()}
                    className="uk-button uk-button-primary uk-float-right"
                >
                    <Icon icon="save" /> Lägg till svarsalternativ
                </button>
            </div>
        );
    }
}

export default QuestionOptionList;
