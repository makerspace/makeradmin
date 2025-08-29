import Base from "Models/Base";
import { useEffect, useMemo, useState } from "react";

export default function useModel<M extends Base<M>>(
    model: { new (): M; get(id: number): any }, // This is an attempt to derive the Model's type from the argument
    id: number,
): M {
    const instance = useMemo(() => model.get(id) as M, [model, id]);
    const [version, setVersion] = useState(0); // Dummy state to force re-render

    useEffect(() => {
        const unsubscribe = instance.subscribe(() => {
            setVersion((v) => v + 1);
        });

        return () => {
            unsubscribe();
        };
    }, [model, id]);

    return instance;
}
