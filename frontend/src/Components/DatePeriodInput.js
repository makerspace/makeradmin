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
        
        return (
            <span>
                <DayPickerInput
                    inputProps={{
                        size: 10,
                        style: {
                            marginTop: "2px",
                            ...(!start && {borderColor: "red"}),
                            ...(historicStart && {color: "brown"}),
                        }
                    }}
                    placeholder="YYYY-MM-DD"
                    value={start || ""}
                    parseDate={parseUtcDate}
                    formatDate={formatUtcDate}
                    onDayChange={d => period.start = d || null}
                />
                &nbsp;-&nbsp;
                <DayPickerInput
                    inputProps={{
                        size: 10,
                        style: {
                            marginTop: "2px",
                            ...(!end && {borderColor: "red"}),
                            ...(historicEnd && {color: "brown"}),
                        }
                    }}
                    placeholder="YYYY-MM-DD"
                    value={end || ""}
                    parseDate={parseUtcDate}
                    formatDate={formatUtcDate}
                    onDayChange={d => period.end = d || null}
                />
            </span>
        );
    }
}


