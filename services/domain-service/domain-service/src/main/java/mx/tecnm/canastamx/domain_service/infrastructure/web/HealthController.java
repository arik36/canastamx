package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.time.Instant;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
            "status",  "UP",
            "service", "domain-service",
            "time",    Instant.now().toString()
        );
    }
}