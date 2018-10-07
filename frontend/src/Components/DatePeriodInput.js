import DayPickerInput from 'react-day-picker/DayPickerInput';
import React from "react";
import {formatUtcDate, parseUtcDate, utcToday} from "../utils";


export default class DatePeriodInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {start: null, end: null};
    }
    
    componentDidMount() {
        const {period} = this.props;
        period.subscribe(() => {
            this.setState({start: period.start, end: period.end});
        });
    }

    render() {
        const {period} = this.props;
        const {start, end} = this.state;

        const today = utcToday();
        const historicStart = start && start < today;
        const historicEnd = end && end < today;
        
        const historicStyle = {color: "grey"};
        
        return (
            <span>
                <span className={period.isDirty("start") ? "ma-changed" : ""}>
                    <DayPickerInput
                        inputProps={{
                            size: 10,
                            className: "uk-input" + (start ? "" : " uk-form-danger"),
                            style: {
                                marginTop: "2px",
                                ...(historicStart &&  historicStyle),
                            }
                        }}
                        placeholder="YYYY-MM-DD"
                        value={start || ""}
                        parseDate={parseUtcDate}
                        formatDate={formatUtcDate}
                        onDayChange={d => period.start = d || null}
                    />
                </span>
                &nbsp;-&nbsp;
                <span className={period.isDirty("start") ? "ma-changed" : ""}>
                    <DayPickerInput
                        inputProps={{
                            className: "uk-input" + (start ? "" : " uk-form-danger") + (period.isDirty("start") ? " ma-input-changed" : ""),
                            size: 10,
                            style: {
                                marginTop: "2px",
                                ...(historicEnd && historicStyle),
                            }
                        }}
                        placeholder="YYYY-MM-DD"
                        value={end || ""}
                        parseDate={parseUtcDate}
                        formatDate={formatUtcDate}
                        onDayChange={d => period.end = d || null}
                    />
                </span>
            </span>
        );
    }
}


