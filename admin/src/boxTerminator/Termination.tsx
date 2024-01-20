import { Button } from "../Components/Button";
import { get } from "../gateway";
import { ActiveLogo } from "./ActiveLogo";
import { ExpiredLogo } from "./ExpiredLogo";

const runAction = (action: string, storage_id: number) => {
    get({
        url: `/box_terminator/action/${action}/${storage_id}`,
    }).then((res) => {
        if (res.status === "ok") {
            alert(res.data);
        }
    });
};

export type TerminationRenderProps = {
    type: string;
    member_number: number;
    member_name: string;
    expired: boolean;
    expired_date: string;
    info?: string;
    storage_id: number;
    options?: [{ text: string; path: string; color: string }];
} | null;

export type TerminationProps = {
    props: TerminationRenderProps;
    callback: () => void;
};

export const Termination = ({ props, callback }: TerminationProps) => {
    if (!props) {
        return null;
    }
    return (
        <div style={{ display: "block" }}>
            <h3>#{props.member_number}</h3>
            <h1>{props.member_name}</h1>
            {props.expired ? (
                <ExpiredLogo width="300px" />
            ) : (
                <ActiveLogo width="300px" />
            )}
            <h1>{props.expired ? "Expired" : "Active"}</h1>
            <h2>Storage type: {props.type}</h2>
            <h3>
                {props.expired
                    ? `expired since: ${props.expired_date}`
                    : `Expires: ${props.expired_date}`}
            </h3>
            {props.info && <h3>{props.info}</h3>}

            {props.options
                ? props.options.map((option) => {
                      return (
                          <Button
                              key={option.text}
                              onClick={() => {
                                  runAction(option.path, props.storage_id);
                              }}
                              style={{ backgroundColor: option.color }}
                          >
                              {option.text}
                          </Button>
                      );
                  })
                : null}

            <Button onClick={callback}>Scan another box</Button>
        </div>
    );
};
