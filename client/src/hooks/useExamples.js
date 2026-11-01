import { useEffect, useState } from "react";
import { chatApi } from "../api/chatApi";

export function useExamples() {
    const [examples, setExamples] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let isCurrent = true;

        chatApi.getExamples()
            .then((items) => {
                if (isCurrent) setExamples(items);
            })
            .catch((requestError) => {
                console.error("Could not load fictional examples:", requestError);
                if (isCurrent) setError(requestError.message);
            })
            .finally(() => {
                if (isCurrent) setLoading(false);
            });

        return () => {
            isCurrent = false;
        };
    }, []);

    return { examples, loading, error };
}
